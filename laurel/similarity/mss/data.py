import ast
import tokenize
import token
from io import StringIO
import keyword
from dataclasses import dataclass
import re

from typing import Tuple

from corexploration.models.openai import OpenAIGateway


@dataclass
class PyToken:
    # these are all `token` type names, plus "KEYWORD" for keywords
    # and "HOLE" for holes
    token_type: str
    string: str
    start: Tuple[int, int]
    end: Tuple[int, int]
    line: str

    def __str__(self) -> str:
        return f"[{token.tok_name[self.exact_type]}, {self.string}, {self.start}, {self.end}]]"

    def from_tokeninfo(tok: tokenize.TokenInfo):
        type_name = token.tok_name[tok.exact_type]
        if keyword.iskeyword(tok.string):
            type_name = "KEYWORD"
        return PyToken(
            token_type=type_name,
            string=tok.string,
            start=tok.start,
            end=tok.end,
            line=tok.line,
        )


class Untokenizer:
    def __init__(self):
        self.tokens = []
        self.prev_row = 0
        self.prev_col = 0

    # Given a (row, col) start position, ensure that the current token list
    # ends at that position
    def add_whitespace(self, start):
        row, col = start
        if row < self.prev_row or (row == self.prev_row and col < self.prev_col):
            raise ValueError("Can't add whitespace in the past")
        row_offset = row - self.prev_row
        if row_offset > 0:
            self.tokens.append("\n" * row_offset)
            self.prev_row += row_offset
            self.prev_col = 0
        col_offset = col - self.prev_col
        if col_offset > 0:
            self.tokens.append(" " * col_offset)
            self.prev_col += col_offset

    def untokenize(self, token_lines: list[list[PyToken]]) -> str:
        self.tokens = []
        self.prev_row = 0
        self.prev_col = 0
        for line in token_lines:
            for tok in line:
                self.add_whitespace(tok.start)
                assert (self.prev_row, self.prev_col) == tok.start
                self.tokens.append(tok.string)
                self.prev_row, self.prev_col = tok.end
        return "".join(self.tokens)


def is_parseable(src: str) -> bool:
    try:
        _ = ast.parse(src)
        return True
    except Exception:
        return False


def clean_completions(prompt: str, model_completions: list[str]) -> list[str]:
    """
    For each of the one of the model completions, keep only the ones that are
    valid python code when appended to the prompt.
    """
    valid_suggestions = []
    not_parseable = 0
    for comp in model_completions:
        if is_parseable(prompt + comp):
            valid_suggestions.append(prompt + comp)
        else:
            print("can't parse:")
            print(prompt + comp, end="\n\n")
            not_parseable += 1
    print(f"Got {not_parseable} not parseable suggestions")
    return valid_suggestions


def get_last_code_snippet(response: str) -> str:
    """
    Given a response from the model, we want to extract the last code snippet from it.
    It could be that the response is bare code, or that it is in Markdown format.
    In the former case, we just return the response, in the latter we extract the last
    code block.
    """
    # If the response is bare code, return it
    if is_parseable(response):
        return response
    # Otherwise, extract the last valid code block
    pattern = r"^```(?:\w+)?\s*\n(.*?)(?=^```)```"
    code_blocks = re.findall(pattern, response, re.DOTALL | re.MULTILINE)
    for block in code_blocks[::-1]:
        if is_parseable(block):
            return block
    return None


def verify_suggestions(prompt: str, model_responses: list[str]) -> list[str]:
    """
    Given a set of LLM suggestions for a given prompt, we need to extract the relevant code snippet
    and verify that
        1) the prompt is a proper prefix of the code snippet
        2) the code snippet is valid python code
    Sometime the model will output the relevant code inside a Markdown code block, so we need to
    extract it.
    There could also be multiple such blocks, in which case we decide to keep only the last one.
    """
    suggestions = []
    invalid = 0
    not_prompt_prefix = 0
    for sugg in model_responses:
        code_snippet = get_last_code_snippet(sugg)
        if code_snippet is None:
            invalid += 1
            continue
        if not code_snippet.startswith(prompt):
            not_prompt_prefix += 1
            continue
        suggestions.append(code_snippet)
    print(f"Got {invalid} invalid suggestions")
    print(f"Got {not_prompt_prefix} suggestions that do not start with the prompt")
    return suggestions


def tokenize_src(src: str) -> list[list[PyToken]]:
    try:
        all_tokens = tokenize.generate_tokens(StringIO(src).readline)
    except Exception:
        return None
    tokenized_lines = []
    current_line = []
    # Split the tokens into lines
    for tok in all_tokens:
        # ignore all non printable tokens
        if tok.type in [token.ENCODING, token.INDENT, token.DEDENT]:
            continue
        if tok.type in [token.NEWLINE, token.ENDMARKER, token.NL]:
            tokenized_lines.append(current_line)
            current_line = []
        else:
            current_line.append(PyToken.from_tokeninfo(tok))
    return tokenized_lines


def untokenize_src(token_lines: list[list[PyToken]]) -> str:
    untk = Untokenizer()
    return untk.untokenize(token_lines)


def tokenize_suggestions(sggs: dict[int, str]) -> list[list[list[str]]]:
    return [tokenize_src(sgg) for sgg in sggs]


def load_suggestions(
    prompt: str, prompt_method: str, **kwargs
) -> Tuple[dict[int, str], list]:
    """
    Given the prompt string, load the suggestions and format them
    to use the clustering algorithm.
    """
    gw = OpenAIGateway(
        spend_money=kwargs.get("spend_money", False),
        debug=kwargs.get("debug", False),
        use_cache=kwargs.get("use_cache", True),
    )
    if prompt_method == "completion":
        model_responses = gw.get_code_completions(prompt, options=kwargs)
        suggestions = clean_completions(prompt, model_responses)
        print(f"Got {len(suggestions)} valid suggestions")
    elif prompt_method == "suggestion":
        model_responses = gw.get_code_suggestions(prompt, options=kwargs)
        suggestions = verify_suggestions(prompt, model_responses)
        print(f"Got {len(suggestions)} valid suggestions")
    else:
        raise ValueError(f"Unknown prompt method {prompt_method}")

    tokenized_suggestions = tokenize_suggestions(suggestions)
    tokenized_suggestions = {i: sg for i, sg in enumerate(tokenized_suggestions)}
    assert max(tokenized_suggestions.keys()) == len(tokenized_suggestions) - 1
    print(f"Got {len(tokenized_suggestions)} tokenized suggestions")

    # return suggestions, tokenized_suggestions
    return suggestions, tokenized_suggestions
