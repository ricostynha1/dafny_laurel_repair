import argparse
import os
import re
import subprocess
import yaml
from datetime import timedelta, time
from llm_prompt import Llm_prompt
from utils import (
    extract_method_or_lemma,
    replace_method,
    extract_method_and_lemma_names,
    adjust_microseconds,
)
from collections import OrderedDict


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


def get_invalid_batches(result_outcome):
    invalid_batches = [
        batch for batch in result_outcome if batch["overall_outcome"] == "Invalid"
    ]
    return invalid_batches


def get_valid_batches_by_time(result_outcome):
    valid_batches = [
        batch for batch in result_outcome if batch["overall_outcome"] == "Valid"
    ]
    sorted_batches = sorted(
        valid_batches, key=lambda x: x["max_batch_time"], reverse=True
    )
    return sorted_batches


def parse_config(config_file):
    with open(config_file, "r") as stream:
        try:
            config_data = yaml.safe_load(stream)
            results_dir = config_data.get("Results_dir")
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            methods_data = config_data.get("Methods", [])

            methods_list = []
            for method_data in methods_data:
                file_path = method_data.get("File_path")
                method_name = method_data.get("Method_name")

                if file_path and method_name:
                    method = Method(file_path, method_name)
                    methods_list.append(method)

            return methods_list, config_data
        except yaml.YAMLError as exc:
            print(exc)


def extract_assertions(code):
    pattern = r"(\bassert\b\s+.+?;\n)"
    matches = re.findall(pattern, code)
    return matches


class Method:
    def __init__(self, file_path, method_name):
        self.file_path = file_path
        self.method_name = method_name
        self.verification_time = None
        self.verification_result = None
        self.error_message = None
        self.dafny_log_file = None

    def create_modified_method(self, new_method, directory):
        new_content = replace_method(
            self.get_file_content(), self.method_name, new_method
        )
        fix_filename = f"{directory}/{self.method_name}_fix.dfy"
        with open(fix_filename, "w") as file:
            file.write(new_content)

        new_method = Method(fix_filename, self.method_name)
        return new_method

    def compare(self, new_method):
        if new_method.verification_result and not self.verification_result:
            return "SUCCESS: Second method verifies, and the first one does not."

        if self.verification_result and new_method.verification_result:
            if new_method.verification_time < self.verification_time:
                return "SUCCESS: Second method verifies faster than the first one."

        return "FAILURE: Second method does not verify."

    def run_verification(self, results_directory):
        dafny_command = [
            "dafny",
            "verify",
            "--boogie-filter",
            f"*{self.method_name}*",
            "--log-format",
            f"text;LogFileName={results_directory}/{self.method_name}.txt",
            self.file_path,
        ]

        self.dafny_log_file = f"{results_directory}/{self.method_name}.txt"

        try:
            subprocess.run(dafny_command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            self.error_message = e.stdout
        self.verification_outcome = parse_assertion_results(self.dafny_log_file)
        self.verification_result = (
            self.verification_outcome[0]["overall_outcome"] == "Correct"
        )
        time_obj = time.fromisoformat(
            adjust_microseconds(self.verification_outcome[0]["overall_time"], 6)
        )
        self.verification_time = timedelta(
            hours=time_obj.hour,
            minutes=time_obj.minute,
            seconds=time_obj.second,
            microseconds=time_obj.microsecond,
        ).total_seconds()

    def __str__(self):
        return f"Method: {self.method_name}\nVerification time: {self.verification_time} seconds\nVerification result: {self.verification_result}"

    def get_file_content(self):
        with open(self.file_path, "r") as file:
            return file.read()

    def get_method_content(self, file_content):
        return extract_method_or_lemma(file_content, self.method_name)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run Dafny verification for specified methods."
    )

    subparsers = parser.add_subparsers(
        dest="mode", help="Choose between llm or remove assertion"
    )

    llm_parser = subparsers.add_parser("llm", help="Use llm mode")
    llm_parser.add_argument("config_file", help="Path to the project")

    prune_assert_parser = subparsers.add_parser(
        "prune-assert", help="Prune-assert mode"
    )
    prune_assert_parser.add_argument("project_path", help="Path to the project")

    return parser.parse_args()


def remove_assertions(project_path, results_path="./results"):
    for root, dirs, files in os.walk(project_path):
        for file in files:
            file_path = os.path.join(root, file)

            with open(file_path) as file:
                content = file.read()

            method_names = extract_method_and_lemma_names(content)
            method_list = []
            for method in method_names:
                method = Method(file_path, method)
                method_list.append(method)
                method.run_verification(results_path)
            sorted_methods = sorted(method_list, key=lambda x: x.verification_time)

            for method in sorted_methods:
                # only in the method
                file_content = method.get_file_content()
                assertions = extract_assertions(method.get_method_content(file_content))
                assertions_time = {}
                for assertion in assertions:
                    modified_method = method.get_method_content(file_content).replace(
                        assertion, "", 1
                    )
                    new_method = method.create_modified_method(
                        modified_method, results_path
                    )
                    new_method.run_verification(results_path)
                    time_difference = float("nan")
                    if new_method.verification_result:
                        time_difference = (
                            method.verification_time - new_method.verification_time
                        )
                    assertions_time[assertion] = time_difference
                    print(new_method)
                # Need to figure out a threshold where we decide that an assertion is usefull or not

    sorted_time_assertions = OrderedDict(
        sorted(assertions_time.items(), key=lambda x: x[1])
    )
    print(sorted_time_assertions)

    pass


def generate_fix_llm(config_file):
    methods, config = parse_config(args.config_file)

    llm_prompt = Llm_prompt(
        config["Prompt"]["System_prompt"], config["Prompt"]["Context"]
    )

    for method in methods:
        print("+--------------------------------------+")
        method.run_verification(config["Results_dir"])
        print(method)
        response = llm_prompt.generate_fix(
            method.file_path,
            method.method_name,
            config["Prompt"]["Fix_prompt"],
            config["Model_parameters"],
        )
        fix_prompt = response["choices"][0]["message"]["content"]
        # TODO extract each assertions separately and count the number of assertions
        # TODO use the new function to replace the method
        # method.create_modified_method(fix_prompt, config["Results_dir"])
        new_method = extract_method_or_lemma(fix_prompt, method.method_name)
        content = method.get_file_content()
        new_content = replace_method(content, method.method_name, new_method)
        fix_filename = f'{config["Results_dir"]}/{method.method_name}_fix.dfy'
        with open(fix_filename, "w") as file:
            file.write(new_content)

        new_method = Method(fix_filename, method.method_name)
        new_method.run_verification(config["Results_dir"])
        print(new_method)
        comparison_result = method.compare(new_method)
        print(comparison_result)


if __name__ == "__main__":
    args = parse_arguments()

    if args.mode == "prune-assert":
        remove_assertions(args.project_path)
    elif args.mode == "llm":
        generate_fix_llm(args.config_file)
