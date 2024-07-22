import re

from utils import extract_line_from_file_content
from placeholder_wrapper import call_placeholder_finder

assertion_placeholder = "\n<assertion> Insert assertion here </assertion>\n"

# def call_placeholder_finder(
#     error_message, method_file, method_name, optional_files=None, blacklisted_file=None
# ):


# mae an equivalent to insert assertion location that just returnt the method with the placeholder
def insert_assertion_location(
    message,
    method_file,
    method_name,
    optional_files=None,
    original_method_file=None,
):
    method_with_placeholder = call_placeholder_finder(
        message,
        method_file,
        method_name,
        optional_files=optional_files,
        blacklisted_file=original_method_file,
    )
    return method_with_placeholder


## Take a dafny error message
## Extract the location at which the assertion should be added
## @Param error_message
# @Return line
# def insert_assertion_location(message, method, file_content):
#     error_message_only = remove_warning(message)
#     match error_message_only:
#         # "assertion might not hold" should always be first as fixing an assertion can fix other kinds of verification errors
#         case _ if "assertion might not hold" in error_message_only:
#             return handle_assertion_might_not_hold(
#                 error_message_only, method, file_content
#             )
#         case (
#             _
#         ) if "precondition for this call could not be proved" in error_message_only:
#             return handle_precondition_not_proved(
#                 error_message_only, method, file_content
#             )
#         case _ if "postcondition could not be proved" in error_message_only:
#             return handle_postcondition_not_proved(
#                 error_message_only, method, file_content
#             )
#         case _ if "possible violation of postcondition of forall" in error_message_only:
#             return handle_possible_violation_postcondition_forall(
#                 method, error_message_only, file_content
#             )
#         case _ if "cannot establish the existence of LHS values" in error_message_only:
#             return handle_cannot_establish_lhs(method, error_message_only, file_content)
#         # TODO what we do for Timeout
#         case _:
#             raise Exception(
#                 f"Type of error message not supported: {error_message_only}"
#             )


def handle_cannot_establish_lhs(method, error_message, file_content):
    """Insert the assertion before the statement"""
    line_number = find_line_number_establish_lhs(error_message)
    line = extract_line_from_file_content(file_content, line_number)
    splitmethod = method.split(line)
    return splitmethod[0] + assertion_placeholder + line + splitmethod[1]


def handle_possible_violation_postcondition_forall(method, error_message, file_content):
    """Not sure about placement, for now insert assertion at the end of the lemma"""
    """placement should be after the open { of the forall """
    line_number = find_line_possible_violation_forall(error_message)
    forall_line = extract_line_from_file_content(file_content, line_number)
    splitmethod = method.split(forall_line)
    return splitmethod[0] + forall_line + "\n" + assertion_placeholder + splitmethod[1]


def handle_precondition_not_proved(error_message, method, file_content):
    """Insert the placeholder before the call where the precondition fails"""
    line_number = find_line_number_call_precondition(error_message)
    line = extract_line_from_file_content(file_content, line_number)
    splitmethod = method.split(line)
    return splitmethod[0] + assertion_placeholder + line + splitmethod[1]


def handle_postcondition_not_proved(error_message, method, file_content):
    """Insert the assertion after the beginning of the path (if or else)
    Note: the location might no be ideal (see LemmaUnionSize)"""
    line_number = find_line_number_path_postcondition(error_message)
    path_line = extract_line_from_file_content(file_content, line_number)
    splitmethod = method.split(path_line)
    return splitmethod[0] + path_line + "\n" + assertion_placeholder + splitmethod[1]


def handle_assertion_might_not_hold(error_message, method, file_content):
    """Insert the placeholder before the assertion that fails"""
    line_number = find_line_number_assertion_might_not_hold(error_message)
    assertion_line = extract_line_from_file_content(file_content, line_number)
    splitmethod = method.split(assertion_line)
    if "by {" in assertion_line:
        # in this case we want to put the placeholder in the assert by
        return (
            splitmethod[0]
            + "\n"
            + assertion_line
            + assertion_placeholder
            + splitmethod[1]
        )
    return splitmethod[0] + assertion_placeholder + assertion_line + splitmethod[1]


def find_line_number_call_precondition(error_message):
    # Regex to match the line number and the code snippet right after the specific error message
    pattern = r"Error: a precondition for this call could not be proved\n\s*\|\n(\d+)\s*\|\s*(.+)\n\s*\|"
    match = re.search(pattern, error_message, re.MULTILINE)

    if match:
        line_number, _ = match.groups()
        return int(line_number)
    else:
        raise Exception("Line number not found")


def find_line_possible_violation_forall(message):
    pattern = (
        r"Error: possible violation of postcondition of forall statement\n\s+\|\n(\d+)"
    )
    match = re.search(pattern, message)
    if match:
        return int(match.group(1))
    else:
        raise Exception("Line number not found")


def find_line_number_establish_lhs(message):
    pattern = r"Error: cannot establish the existence of LHS values that satisfy the such-that predicate\n\s+\|\n(\d+)"
    match = re.search(pattern, message)
    if match:
        return int(match.group(1))
    else:
        raise Exception("Line number not found")


def find_line_number_assertion_might_not_hold(message):
    pattern = r"Error: assertion might not hold\n\s+\|\n(\d+)"
    match = re.search(pattern, message)
    if match:
        return int(match.group(1))
    else:
        raise Exception("Line number not found")


def find_line_number_path_postcondition(text):
    pattern = (
        r"Error: a postcondition could not be proved on this return path\n\s+\|\n(\d+)"
    )
    match = re.search(pattern, text)
    if match:
        return int(match.group(1))
    raise Exception("Line number not found")


def remove_warning(message):
    lines = message.split("\n")

    # Find the index of the first line containing an error
    error_index = next(
        (i for i, line in enumerate(lines) if "Error" in line), len(lines)
    )
    filtered_lines = lines[error_index:]
    return "\n".join(filtered_lines)
