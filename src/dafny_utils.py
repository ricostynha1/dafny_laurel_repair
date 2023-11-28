import re


def parse_assertion_results(file_path):
    with open(file_path, "r") as f:
        data = f.read()
    assertion_batches = re.split(r"\n(?=\s*Results for \w+)", data)[1:]

    result = []
    for batch in assertion_batches:
        if not batch:
            continue
        function_match = re.search(r"Results for (\w+) \((\w+)\)", batch)
        if function_match:
            function_name = function_match.group(1)
            verification_type = function_match.group(2)
        else:
            function_name = None
            verification_type = None

        overall_outcome_match = re.search(r"Overall outcome: (\w+)", batch)
        overall_time_match = re.search(r"Overall time: (.+)", batch)
        overall_resource_count_match = re.search(
            r"Overall resource count: (\d+)", batch
        )
        max_batch_time_match = re.search(r"Maximum assertion batch time: (.+)", batch)
        max_batch_resource_count_match = re.search(
            r"Maximum assertion batch resource count: (\d+)", batch
        )
        batch_info_matches = re.finditer(
            r"Assertion batch (\d+):([\s\S]*?)(?=\n\s*Assertion batch \d+|$)", batch
        )

        batches_info = []
        for batch_info_match in batch_info_matches:
            batch_number = int(batch_info_match.group(1))
            batch_info = batch_info_match.group(2).strip()

            outcome_match = re.search(r"Outcome: (\w+)", batch_info)
            duration_match = re.search(r"Duration: (.+)", batch_info)
            resource_count_match = re.search(r"Resource count: (\d+)", batch_info)

            batch_data = {
                "batch_number": batch_number,
                "overall_outcome": outcome_match.group(1) if outcome_match else None,
                "duration": duration_match.group(1) if duration_match else None,
                "resource_count": int(resource_count_match.group(1))
                if resource_count_match
                else None,
            }

            assertions_info = []
            assertions_matches = re.finditer(
                r"(\w+\.\w+)\((\d+),(\d+)\): (.+)", batch_info
            )
            for match in assertions_matches:
                file_name, line, character, assertion_result = match.groups()

                assertions_info.append(
                    {
                        "filename": file_name,
                        "line": int(line),
                        "character": int(character),
                        "assertion_result": assertion_result,
                    }
                )

            batch_data["assertions"] = assertions_info
            batches_info.append(batch_data)

        function_data = {
            "function_name": function_name,
            "verification_type": verification_type,
            "overall_outcome": overall_outcome_match.group(1)
            if overall_outcome_match
            else None,
            "overall_time": overall_time_match.group(1) if overall_time_match else None,
            "overall_resource_count": int(overall_resource_count_match.group(1))
            if overall_resource_count_match
            else None,
            "max_batch_time": max_batch_time_match.group(1)
            if max_batch_time_match
            else None,
            "max_batch_resource_count": int(max_batch_resource_count_match.group(1))
            if max_batch_resource_count_match
            else None,
            "batches": batches_info,
        }

        result.append(function_data)

    return result


def extract_assertions(code):
    pattern = r"(\bassert\b\s+.+?;\n)"
    matches = re.findall(pattern, code)
    return matches


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

            # hack to identify when a function finishes
            # {} if it is an empty function
            # otherwise expect } and with a brace count to 0 (since we are finishing the func)
            # and not an even number of braces on the line (the odd is the one to finish the func)
            if (
                brace_count == 0
                and "}" in line
                and (brace_line_count != 0 or "{}" in line)
            ):
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
