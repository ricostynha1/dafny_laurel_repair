import argparse
import csv
import os
import re
import subprocess
import time
import yaml
import datetime
from llm_prompt import Llm_prompt
from logger_config import logger
from utils import (
    extract_dafny_functions,
    replace_method,
    extract_method_and_lemma_names,
    adjust_microseconds,
)


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


def parse_config_assert_pruning(config_file):
    with open(config_file, "r") as stream:
        try:
            config_data = yaml.safe_load(stream)
            return config_data
        except yaml.YAMLError as exc:
            logger.error(exc)


def parse_config_llm(config_file):
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
            logger.error(exc)


def extract_assertions(code):
    pattern = r"(\bassert\b\s+.+?;\n)"
    matches = re.findall(pattern, code)
    return matches


class Method:
    def __init__(self, file_path, method_name, index=0):
        self.file_path = file_path
        self.method_name = method_name
        self.verification_time = None
        self.verification_result = None
        self.error_message = None
        self.dafny_log_file = None
        self.index = index

    # the directory needs to be where the previous file is
    # otherwise the dependencies won't work
    def create_modified_method(self, new_method, directory, index):
        new_content = replace_method(
            self.get_file_content(), self.method_name, new_method
        )
        fix_filename = f"{directory}/{self.method_name}_fix_{index}.dfy"
        with open(fix_filename, "w") as file:
            file.write(new_content)

        new_method = Method(fix_filename, self.method_name, index=index)
        return new_method

    def compare(self, new_method):
        if new_method.verification_result and not self.verification_result:
            return "SUCCESS: Second method verifies, and the first one does not."

        if self.verification_result and new_method.verification_result:
            if new_method.verification_time < self.verification_time:
                return "SUCCESS: Second method verifies faster than the first one."

        return "FAILURE: Second method does not verify."

    def run_verification(self, results_directory, additionnal_args=None):
        dafny_command = [
            "dafny",
            "verify",
            "--boogie-filter",
            f"*{self.method_name}*",
            "--log-format",
            f"text;LogFileName={results_directory}/{self.method_name}.txt",
            self.file_path,
        ]
        dafny_command[-1:-1] = additionnal_args.split() if additionnal_args else []
        logger.debug(dafny_command)

        self.dafny_log_file = f"{results_directory}/{self.method_name}.txt"

        try:
            result = subprocess.run(
                dafny_command, check=True, capture_output=True, text=True
            )
            logger.debug(result.stdout)
        except subprocess.CalledProcessError as e:
            self.error_message = e.stdout
            logger.error(e.stdout)
            logger.error(e.stderr)
        self.verification_outcome = parse_assertion_results(self.dafny_log_file)
        if not self.verification_outcome:
            return False
        self.verification_result = (
            self.verification_outcome[0]["overall_outcome"] == "Correct"
        )
        try:
            time_adjusted = adjust_microseconds(
                self.verification_outcome[0]["overall_time"], 6
            )
            time_obj = datetime.time.fromisoformat(time_adjusted)
        except ValueError as e:
            logger.error(e)
            logger.error(time_adjusted)

        self.verification_time = datetime.timedelta(
            hours=time_obj.hour,
            minutes=time_obj.minute,
            seconds=time_obj.second,
            microseconds=time_obj.microsecond,
        ).total_seconds()
        return True

    def __str__(self):
        return f"Method: {self.method_name} in {self.file_path}\nVerification time: {self.verification_time} seconds\nVerification result: {self.verification_result}"

    def get_file_content(self):
        with open(self.file_path, "r") as file:
            return file.read()

    def get_method_content(self, file_content):
        return extract_dafny_functions(file_content, self.method_name)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run Dafny verification for specified methods."
    )

    subparsers = parser.add_subparsers(
        dest="mode", help="Choose between llm or remove assertion"
    )

    llm_parser = subparsers.add_parser("llm", help="Use llm mode")
    llm_parser.add_argument("config_file", help="Config to run the llm gen")

    prune_assert_parser = subparsers.add_parser(
        "prune-assert", help="Prune-assert mode"
    )
    prune_assert_parser.add_argument("config_file", help="Config to run the llm gen")

    return parser.parse_args()


def write_csv_header(csv_file_path):
    header = [
        "Index",
        "File",
        "Method",
        "Assertion",
        "Time difference",
        "New method time",
        "New method result",
    ]
    csv_file = open(csv_file_path, "a", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(header)
    return csv_writer


def remove_assertions(config_file):
    config = parse_config_assert_pruning(config_file)
    project_path = config["Project_path"]
    results_path = config["Results_dir"]
    stats_file = config["Stats_file"]

    total_files = sum(
        1
        for _, _, files in os.walk(project_path)
        for file in files
        if file.endswith(".dfy") and "_fix" not in file
    )
    file_counter = 0
    start_time = time.time()

    method_index = 0
    stats = []
    csv_writer = write_csv_header(stats_file)
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith(".dfy") and "_fix" not in file:
                file_counter += 1

                file_path = os.path.join(root, file)
                file_location = os.path.dirname(file_path)
                logger.info(f"Starting file {file_counter}/{total_files}:{file_path}")

                with open(file_path) as file:
                    content = file.read()

                method_names = extract_method_and_lemma_names(content)
                method_list = []
                success = True
                for method in method_names:
                    try:
                        method = Method(file_path, method)
                        method_list.append(method)
                        success = method.run_verification(
                            results_path, additionnal_args=config["Dafny_args"]
                        )
                        if not success:
                            method.verification_time = 0
                            continue
                    except Exception as e:
                        logger.error(e)
                        continue

                if success:
                    sorted_methods = sorted(
                        method_list, key=lambda x: x.verification_time
                    )
                else:
                    continue

                for method in sorted_methods:
                    try:
                        file_content = method.get_file_content()
                        assertions = extract_assertions(
                            method.get_method_content(file_content)
                        )
                        for assertion in assertions:
                            method_index += 1
                            modified_method = method.get_method_content(
                                file_content
                            ).replace(assertion, "", 1)
                            new_method = method.create_modified_method(
                                modified_method, file_location, method_index
                            )
                            success = new_method.run_verification(
                                results_path, additionnal_args=config["Dafny_args"]
                            )
                            if not success:
                                continue
                            time_difference = float("nan")
                            if new_method.verification_result:
                                time_difference = (
                                    method.verification_time
                                    - new_method.verification_time
                                )
                            assertions_stats = [
                                new_method.index,
                                method.file_path,
                                method.method_name,
                                assertion,
                                time_difference,
                                new_method.verification_time,
                                new_method.verification_result,
                            ]
                            logger.info(new_method)
                            stats.append(assertions_stats)
                            csv_writer.writerow(assertions_stats)
                    except Exception as e:
                        logger.error(e)
                        continue

                    # TODO Need to figure out a threshold where we decide that an assertion is usefull or not
                elapsed_time = time.time() - start_time
                logger.info(
                    f"====Finished file {file_path} {file_counter}/{total_files} after {elapsed_time} seconds====="
                )


def generate_fix_llm(config_file):
    methods, config = parse_config_llm(args.config_file)

    llm_prompt = Llm_prompt(
        config["Prompt"]["System_prompt"], config["Prompt"]["Context"]
    )

    for method in methods:
        logger.info("+--------------------------------------+")
        method.run_verification(config["Results_dir"])
        logger.info(method)
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
        new_method = extract_dafny_functions(fix_prompt, method.method_name)
        content = method.get_file_content()
        new_content = replace_method(content, method.method_name, new_method)
        # TODO FIX "results_dir" might not work here since the file will miss its dependencies
        fix_filename = f'{config["Results_dir"]}/{method.method_name}_fix.dfy'
        with open(fix_filename, "w") as file:
            file.write(new_content)

        new_method = Method(fix_filename, method.method_name)
        new_method.run_verification(config["Results_dir"])
        logger.info(new_method)
        comparison_result = method.compare(new_method)
        logger.info(comparison_result)


if __name__ == "__main__":
    args = parse_arguments()

    if args.mode == "prune-assert":
        logger.info("==== Starting the assertion pruning ====")
        remove_assertions(args.config_file)
    elif args.mode == "llm":
        logger.info("==== Starting the llm fix ====")
        generate_fix_llm(args.config_file)
