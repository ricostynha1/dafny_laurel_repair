import openai
import os
import re

openai.api_key = os.getenv("OPENAI_API_KEY")


class Llm_prompt:
    def __init__(self, system_prompt, context):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        for examples in context:
            with open(examples["File_to_fix"], "r") as f:
                # remove the last line since it is the code url
                # TODO clean that
                code_to_fix = "\n".join(f.read().split("\n")[:-1])
            user_content = f"{examples['Question_prompt']} {code_to_fix}"

            with open(examples["Fix"], "r") as f:
                # remove the last line since it is the code url
                # TODO clean that
                fix = "\n".join(f.read().split("\n")[:-1])
            assistant_content = f"{examples['Answer_prompt']} {fix}"

            messages.append({"role": "user", "content": user_content})
            messages.append({"role": "assistant", "content": assistant_content})
        self.messages = messages

    def extract_method_or_lemma(self, file_path, name):
        with open(file_path, "r") as f:
            content = f.read()
        method_pattern = re.compile(rf"method {name}[^)]*\)(.*?\}})", re.DOTALL)
        method_match = method_pattern.search(content)

        lemma_pattern = re.compile(rf"lemma {name}[^)]*\)(.*?\}})", re.DOTALL)
        lemma_match = lemma_pattern.search(content)

        if method_match:
            return method_match.group(0).strip()
        elif lemma_match:
            return lemma_match.group(0).strip()
        else:
            return None

    def generate_fix(self, program_to_fix, method_name, fix_prompt, model_parameters):
        method = self.extract_method_or_lemma(program_to_fix, method_name)
        question = f"{fix_prompt} {method}"

        self.messages.append({"role": "user", "content": question})
        response = openai.ChatCompletion.create(
            model=model_parameters["Model"],
            temperature=model_parameters["Temperature"],
            max_tokens=model_parameters["Max_tokens"],
            messages=self.messages,
        )
        return response
