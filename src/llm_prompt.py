import logging
import json
import openai
import os
import tiktoken
from dafny_utils import extract_dafny_functions
from guidance import system, user, assistant, models

from error_parser import insert_assertion_location

openai.api_key = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)


class Llm_prompt:
    def __init__(self, system_prompt, context):
        model = models.OpenAI("gpt-4", echo=False)
        messages = []
        chat = model
        if system_prompt:
            with system():
                messages.append({"role": "system", "content": system_prompt})
                chat += system_prompt
        for examples in context:
            with open(examples["File_to_fix"], "r") as f:
                # remove the last line since it is the code url
                # TODO clean that
                code_to_fix = "\n".join(f.read().split("\n")[:-1])
            user_content = (
                f"{examples['Question_prompt']}\n<method>\n{code_to_fix}\n</method>"
            )

            with open(examples["Fix"], "r") as f:
                # remove the last line since it is the code url
                # TODO clean that
                fix = "\n".join(f.read().split("\n")[:-1])
            assistant_content = f"{examples['Answer_prompt']} {fix}"

            with user():
                chat += user_content
            with assistant():
                chat += assistant_content
            messages.append({"role": "user", "content": user_content})
            messages.append({"role": "assistant", "content": assistant_content})
        self.chat = chat
        self.messages = messages

    def add_question(
        self,
        program_to_fix,
        method_name,
        error_message,
        fix_prompt,
        model_parameters,
        context_option,
        feedback,
    ):
        with open(program_to_fix, "r") as f:
            content = f.read()
        method = extract_dafny_functions(content, method_name)
        # Everything but the method
        context = content.replace(method, "")

        # current size =
        current_prompt_length = self.get_prompt_length(model_parameters["Encoding"])
        encoding = tiktoken.get_encoding(model_parameters["Encoding"])
        num_tokens_method = len(encoding.encode(method))
        num_tokens_fix_prompt = len(encoding.encode(fix_prompt))
        current_prompt_length += num_tokens_method + num_tokens_fix_prompt
        # depending on feedback included add the feedback
        method_with_placeholder = insert_assertion_location(
            error_message, method, content
        )
        question = f"{fix_prompt}\n <method> {method_with_placeholder} </method>"
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
        return method_with_placeholder

    def feedback_error_message(self, error_message):
        error_feedback = (
            "This is the new error message that we get after the indicated change:\n <error>\n"
            + error_message
            + "\n <\error>"
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
