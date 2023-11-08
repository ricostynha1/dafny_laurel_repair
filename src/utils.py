import re


def extract_method_or_lemma(content, name):
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


def extract_method_and_lemma_names(content):
    method_names = re.findall(r"\bmethod\s+(\w+)", content)
    lemma_names = re.findall(r"\blemma\s+(\w+)", content)

    return method_names + lemma_names


def replace_method(file_content, old_method_name, new_method_content):
    old_method_pattern = re.compile(
        rf"method {old_method_name}[^)]*\)(.*?\}})", re.DOTALL
    )
    old_method_match = old_method_pattern.search(file_content)
    lemma_pattern = re.compile(rf"lemma {old_method_name}[^)]*\)(.*?\}})", re.DOTALL)
    lemma_match = lemma_pattern.search(file_content)

    if old_method_match:
        modified_content = old_method_pattern.sub(new_method_content, file_content)
        print(f"Method '{old_method_name}' replaced successfully.")
    elif lemma_match:
        modified_content = lemma_pattern.sub(new_method_content, file_content)
        print(f"Lemma'{old_method_name}' replaced successfully.")
    else:
        print(f"Method '{old_method_name}' not found in the file.")
    return modified_content


def adjust_microseconds(time_str, desired_precision):
    seconds, microseconds = time_str.split(".")

    rounded_microseconds = str(round(float(f"0.{microseconds}"), desired_precision))[2:]
    padded_microseconds = rounded_microseconds.ljust(desired_precision, "0")

    adjusted_time_str = f"{seconds}.{padded_microseconds}"

    return adjusted_time_str
