from placeholder_wrapper import call_placeholder_finder


# insert assertion location that just return the method with the placeholder
def insert_assertion_location(
    message,
    method_file,
    method_name,
    optional_files=None,
    original_method_file=None,
    multiple_locations=False,
):
    method_with_placeholder = call_placeholder_finder(
        remove_warning(message),
        method_file,
        method_name,
        optional_files=optional_files,
        blacklisted_file=original_method_file,
        multiple_locations=multiple_locations,
    )
    return method_with_placeholder


def remove_warning(message):
    lines = message.split("\n")

    # Find the index of the first line containing an error
    error_index = next(
        (i for i, line in enumerate(lines) if "Error" in line), len(lines)
    )
    filtered_lines = lines[error_index:]
    return "\n".join(filtered_lines)
