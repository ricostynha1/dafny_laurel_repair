## Take a dafny error message
## Extract the location at which the assertion should be added
## @Param error_message
# @Return line
def get_assertion_location(message):
    print("______________")
    error_message_only = remove_warning(message)
    print(error_message_only)


# def handle_assertion_might_not_hold(message):
#


def remove_warning(message):
    lines = message.split("\n")

    # Find the index of the first line containing an error
    error_index = next(
        (i for i, line in enumerate(lines) if "Error" in line), len(lines)
    )
    filtered_lines = lines[error_index:]
    return "\n".join(filtered_lines)
