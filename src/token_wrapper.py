import subprocess
import os

TOKENIZER_CSHARP_PATH = "tokenizer_csharp/bin/Debug/net6.0/tokenizer_csharp"


def call_tokenizer_csharp(code):
    command = [
        os.path.dirname(__file__)
        + "/tokenizer_csharp/bin/Debug/net6.0/tokenizer_csharp"
    ]
    result = subprocess.run(
        command, input=code, capture_output=True, text=True, check=True
    )
    output = result.stdout.strip()
    return output


## Tranform the JSON into a list of list of tokens
## Example:
## [[{"Item1":"35","Item2":"assert"},{"Item1":"146","Item2":"false"},{"Item1":"32","Item2":";"},{"Item1":"0","Item2":""}]]
## to
## [[("35", "assert"), ("146", "false"), ("32", ";"), ("0", "")]]
def parse_token_output(output):
    tokens = eval(output)
    return [[(t["Item1"], t["Item2"]) for t in token] for token in tokens]


# Example usage:
# code = "assert xs + xy == xy;"
# json_ouput = call_tokenizer_csharp(code)
# print(parse_token_output(json_ouput))
