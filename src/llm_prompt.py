import openai
import os
from utils import extract_dafny_functions

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

    def generate_fix(self, program_to_fix, method_name, fix_prompt, model_parameters):
        with open(program_to_fix, "r") as f:
            content = f.read()
        method = extract_dafny_functions(content, method_name)
        question = f"{fix_prompt} {method}"

        self.messages.append({"role": "user", "content": question})
        response = openai.ChatCompletion.create(
            model=model_parameters["Model"],
            temperature=model_parameters["Temperature"],
            max_tokens=model_parameters["Max_tokens"],
            messages=self.messages,
        )
        return response
