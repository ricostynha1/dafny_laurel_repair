import re


assertion_placeholder = "<assertion> Insert assertion here </assertion>\n"


## Take a dafny error message
## Extract the location at which the assertion should be added
## @Param error_message
# @Return line
def insert_assertion_location(message, method):
    print("______________")
    error_message_only = remove_warning(message)
    print(error_message_only)
    lm = handle_assertion_might_not_hold(error_message_only, method)
    return lm


def handle_assertion_might_not_hold(error_message, method):
    # Extract the assertion from the error
    assertion = extract_assertion_might_not_hold(error_message)
    splitmethod = method.split(assertion)
    # We loose the identation of assertion here!
    return splitmethod[0] + assertion_placeholder + assertion + splitmethod[1]


def extract_assertion_might_not_hold(message):
    lines = message.split("\n")
    for line in lines:
        if re.match("^\d+\s+\|", line):
            assertion_line = line

    assertion = assertion_line.split("|")[1].strip()
    return assertion


def remove_warning(message):
    lines = message.split("\n")

    # Find the index of the first line containing an error
    error_index = next(
        (i for i, line in enumerate(lines) if "Error" in line), len(lines)
    )
    filtered_lines = lines[error_index:]
    return "\n".join(filtered_lines)
