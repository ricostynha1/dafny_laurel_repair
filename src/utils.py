import re


def extract_dafny_functions(dafny_code, name):
    inside_function = False
    current_function = ""
    brace_count = 0

    lines = dafny_code.split("\n")

    for line in lines:
        if f"lemma {name}" in line or f"method {name}" in line:
            inside_function = True
            current_function += line + "\n"
            brace_count += line.count("{") - line.count("}")
        elif inside_function:
            current_function += line + "\n"
            brace_line_count = line.count("{") - line.count("}")
            brace_count += brace_line_count

            if brace_count == 0 and "}" in line and brace_line_count != 0:
                inside_function = False
                return current_function


def extract_method_and_lemma_names(content):
    method_names = re.findall(r"\bmethod\s+(\w+)", content)
    lemma_names = re.findall(r"\blemma\s+(\w+)", content)

    return method_names + lemma_names


def replace_method(file_content, old_method_name, new_method_content):
    function = extract_dafny_functions(file_content, old_method_name)
    dafny_code = file_content.replace(function, new_method_content)
    return dafny_code


def adjust_microseconds(time_str, desired_precision):
    seconds, microseconds = time_str.split(".")

    rounded_microseconds = str(round(float(f"0.{microseconds}"), desired_precision))[2:]
    padded_microseconds = rounded_microseconds.ljust(desired_precision, "0")

    adjusted_time_str = f"{seconds}.{padded_microseconds}"

    return adjusted_time_str
