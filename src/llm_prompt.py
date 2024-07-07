import logging
import json
import openai
import tiktoken
import yaml
from dafny_utils import extract_dafny_functions
from guidance import system, user, assistant, models

from error_parser import insert_assertion_location
from utils import string_difference


logger = logging.getLogger(__name__)


class Llm_prompt:
    def __init__(self, system_prompt, example_selector):
        with open(".secrets.yaml", "r") as f:
            secrets = yaml.safe_load(f)
        openai.api_key = secrets["OPENAI_API_KEY"]
        model = models.OpenAI("gpt-4", echo=False, api_key=secrets["OPENAI_API_KEY"])
        messages = []
        chat = model
        if system_prompt:
            with system():
                messages.append({"role": "system", "content": system_prompt})
                chat += system_prompt
        if example_selector is not None and example_selector.nature != "Dynamic":
            for example in example_selector.examples:
                with user():
                    chat += example["Question"]
                with assistant():
                    chat += example["Answer"]
                messages.append({"role": "user", "content": example["Question"]})
                messages.append({"role": "assistant", "content": example["Answer"]})

        self.chat = chat
        self.messages = messages

    def remove_answer(self, method_content, method_name):
        messages_copy = self.messages.copy()
        for i, message in enumerate(messages_copy):
            if message["role"] == "user":
                extracted_method = extract_dafny_functions(
                    message["content"], method_name
                )
                if extracted_method is not None:
                    diff = string_difference(method_content, extracted_method)
                    diff = diff.replace(
                        "<assertion> Insert the assertion here </assertion>\n", ""
                    )
                    self.messages[i]["content"] = self.messages[i]["content"].replace(
                        diff, ""
                    )

    def add_question(
        self,
        program_to_fix,
        method_name,
        error_message,
        fix_prompt,
        model_parameters,
        context_option,
        feedback,
        example_selector,
        threshold,
        placeholder,
    ):
        with open(program_to_fix, "r") as f:
            content = f.read()
        method = extract_dafny_functions(content, method_name)
        examples = []
        if example_selector.nature == "Dynamic":
            examples = example_selector.generate_dynamic_examples(
                method, threshold, fix_prompt, program_to_fix
            )
        for example in examples:
            with user():
                self.chat += example["Question"]
            with assistant():
                self.chat += example["Answer"]
            self.messages.append({"role": "user", "content": example["Question"]})
            self.messages.append({"role": "assistant", "content": example["Answer"]})
        # Everything but the method
        self.remove_answer(method, method_name)
        context = content.replace(method, "")

        # current size =
        current_prompt_length = self.get_prompt_length(model_parameters["Encoding"])
        encoding = tiktoken.get_encoding(model_parameters["Encoding"])
        num_tokens_method = len(encoding.encode(method))
        num_tokens_fix_prompt = len(encoding.encode(fix_prompt))
        current_prompt_length += num_tokens_method + num_tokens_fix_prompt
        # depending on feedback included add the feedback
        method_to_insert = method
        if placeholder:
            method_to_insert = insert_assertion_location(error_message, method, content)
        question = f"{fix_prompt}\n <method> {method_to_insert} </method>"
        if feedback:
            num_tokens_feedback = len(encoding.encode(feedback))
            current_prompt_length += num_tokens_feedback
            question += f"\n\n<error>\n{feedback}\n</error>"
            logger.debug(f"Feedback added: {num_tokens_feedback}")

        # if context enabled:
        if context_option == "File":
            encoded_context = encoding.encode(context)
            num_tokens_context = len(encoded_context)
            if (
                current_prompt_length
                + num_tokens_context
                + model_parameters["Max_tokens"]
                + 100
                > model_parameters["Prompt_limit"]
            ):
                # cut the context up to the limit
                token_limit = (
                    model_parameters["Prompt_limit"]
                    - current_prompt_length
                    - model_parameters["Max_tokens"]
                    - 100
                )
                encoded_context = encoded_context[:token_limit]
                context = encoding.decode(encoded_context)
                question += f"\n Context of the method: \n {context}"

        with user():
            self.chat += question
        self.messages.append({"role": "user", "content": question})
        return method_to_insert

    def feedback_error_message(self, error_message):
        error_feedback = (
            "This is the new error message that we get after the indicated change:\n <error>\n"
            + error_message
            + "\n <\\error>"
        )
        with user():
            self.chat += error_feedback
        self.messages.append({"role": "user", "content": error_feedback})

    def save_prompt(self, path):
        with open(path, "w") as f:
            json.dump(self.messages, f)

    def get_prompt_length(self, encoding_name):
        encoding = tiktoken.get_encoding(encoding_name)
        content_string = "".join(item["content"] for item in self.messages)
        num_tokens = len(encoding.encode(content_string))
        return num_tokens

    def get_fix(self, model_parameters):
        fix = self.generate_fix(model_parameters)
        self.messages.append({"role": "assistant", "content": fix})
        return fix

    def generate_fix(self, model_parameters):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "insert_dafny_assertion",
                    "description": "Use this function to insert a Dafny assertion into a predefined placeholder.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "assertion": {
                                "type": "string",
                                "description": "The Dafny assertion to insert into the placeholder.",
                            }
                        },
                        "required": ["assertion"],
                    },
                },
            }
        ]
        response = openai.chat.completions.create(
            model=model_parameters["Model"],
            temperature=model_parameters["Temperature"],
            max_tokens=model_parameters["Max_tokens"],
            messages=self.messages,
            tools=tools,
            tool_choice={
                "type": "function",
                "function": {"name": "insert_dafny_assertion"},
            },
        )

        return json.loads(response.choices[0].message.tool_calls[0].function.arguments)[
            "assertion"
        ]
