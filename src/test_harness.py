import argparse
import os
import shutil
from llm_prompt import Llm_prompt
from logger_config import configure_logger
from dafny_utils import (
    extract_dafny_functions,
)
from utils import read_pruning_result
from config_parsing import parse_config_llm
from pruning import remove_assertions

from Method import Method


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run Dafny verification for specified methods."
    )
    parser.add_argument(
        "--disable_date", action="store_true", help="remove date from logs"
    )

    # parser.add_argument("-log_date", "-ld", help="remove date from logs")

    subparsers = parser.add_subparsers(
        dest="mode", help="Choose between llm or remove assertion"
    )

    llm_parser = subparsers.add_parser("llm", help="Use llm mode")
    llm_parser.add_argument("config_file", help="Config to run the llm gen")
    llm_parser.add_argument("--pruning_results", "-p", help="CSV pruning results file")

    prune_assert_parser = subparsers.add_parser(
        "prune-assert", help="Prune-assert mode"
    )
    prune_assert_parser.add_argument("config_file", help="Config to run the llm gen")

    return parser.parse_args()


def generate_fix_llm(config_file, pruning_results=None):
    methods = []
    new_file_location = None
    if pruning_results:
        method_processed = 0
        success_count = 0
        _, config = parse_config_llm(config_file)
        llm_prompt = Llm_prompt(
            config["Prompt"]["System_prompt"], config["Prompt"]["Context"]
        )
        for row in pruning_results:
            # copy the original
            if "DivModAddDenominator_fix_2" in row["File new method"]:
                continue
            original_filepath = row["File"]
            new_file_location = shutil.move(
                original_filepath,
                f"{config['Results_dir']}/{os.path.basename(original_filepath)}",
            )
            # move the file new method to the original
            # but just extract the location
            original_path = os.path.dirname(original_filepath)
            file_to_fix = os.path.basename(row["File new method"])
            actual_filepath_to_fix = os.path.join(config["Results_dir"], file_to_fix)
            filepath_to_fix = os.path.join(original_path, file_to_fix)
            shutil.copy(actual_filepath_to_fix, filepath_to_fix)
            method = Method(filepath_to_fix, row["Method"])
            logger.info("+--------------------------------------+")
            if "Dafny_args" in config:
                method.run_verification(
                    config["Results_dir"], additionnal_args=config["Dafny_args"]
                )
            else:
                method.run_verification(config["Results_dir"])
            logger.debug(method)
            try:
                response = llm_prompt.generate_fix(
                    method.file_path,
                    method.method_name,
                    config["Prompt"]["Fix_prompt"],
                    config["Model_parameters"],
                )
                fix_prompt = response["choices"][0]["message"]["content"]
                # TODO extract each assertions separately and count the number of assertions
                new_method_content = extract_dafny_functions(
                    fix_prompt, method.method_name
                )
                logger.debug(new_method_content)
                new_method_content = "\n".join(
                    line.lstrip("+") for line in new_method_content.splitlines()
                )
                method_location = os.path.dirname(method.file_path)
                new_method = method.create_modified_method(
                    new_method_content, method_location, 0
                )
                # remove previous method
                method.move_to_results_directory(config["Results_dir"])
                if "Dafny_args" in config:
                    new_method.run_verification(
                        config["Results_dir"], additionnal_args=config["Dafny_args"]
                    )
                else:
                    new_method.run_verification(config["Results_dir"])
                logger.debug(new_method)
                comparison_result, comparison_details = method.compare(new_method)
                new_method.move_to_results_directory(config["Results_dir"])
                logger.info(comparison_details)
                if comparison_result:
                    success_count += 1
            except Exception as e:
                print(e)
            # copy the original method from the result dir
            shutil.copy(new_file_location, original_filepath)
            shutil.copy(actual_filepath_to_fix, filepath_to_fix)

            method_processed += 1
            logger.info(f"Succes rate: {success_count}/{method_processed}")
    else:
        methods, config = parse_config_llm(config_file)

        llm_prompt = Llm_prompt(
            config["Prompt"]["System_prompt"], config["Prompt"]["Context"]
        )

        method_processed = 0
        success_count = 0
        for method in methods:
            logger.info("+--------------------------------------+")
            if "Dafny_args" in config:
                method.run_verification(
                    config["Results_dir"], additionnal_args=config["Dafny_args"]
                )
            else:
                method.run_verification(config["Results_dir"])
            logger.debug(method)
            response = llm_prompt.generate_fix(
                method.file_path,
                method.method_name,
                config["Prompt"]["Fix_prompt"],
                config["Model_parameters"],
            )
            fix_prompt = response["choices"][0]["message"]["content"]
            # TODO extract each assertions separately and count the number of assertions
            new_method_content = extract_dafny_functions(fix_prompt, method.method_name)
            logger.debug(new_method_content)
            new_method_content = "\n".join(
                line.lstrip("+") for line in new_method_content.splitlines()
            )
            method_location = os.path.dirname(method.file_path)
            # method_location = method.file_path
            # tmp_path_original = method.move_to_results_directory(config["Results_dir"])
            tmp_path_original = shutil.copy(
                method.file_path,
                f"{config['Results_dir']}/{os.path.basename(method.file_path)}",
            )
            new_method = method.create_modified_method(
                new_method_content, method_location, 0
            )
            # remove previous method
            if "Dafny_args" in config:
                new_method.run_verification(
                    config["Results_dir"], additionnal_args=config["Dafny_args"]
                )
            else:
                new_method.run_verification(config["Results_dir"])
            logger.debug(new_method)
            comparison_result, comparison_details = method.compare(new_method)
            new_method.move_to_results_directory(config["Results_dir"])
            # copy the original method from the result dir
            shutil.copy(tmp_path_original, method.file_path)

            logger.info(comparison_details)
            method_processed += 1
            if comparison_result:
                success_count += 1
            logger.info(f"Succes rate: {success_count}/{method_processed}")


if __name__ == "__main__":
    args = parse_arguments()
    if args.disable_date:
        logger = configure_logger(include_date=False)
    else:
        logger = configure_logger()

    if args.mode == "prune-assert":
        logger.info("==== Starting the assertion pruning ====")
        remove_assertions(args.config_file)
    elif args.mode == "llm":
        logger.info("==== Starting the llm fix ====")
        if args.pruning_results:
            methods = []
            pruning_results = read_pruning_result(args.pruning_results)
            generate_fix_llm(args.config_file, pruning_results=pruning_results)
        else:
            generate_fix_llm(args.config_file)
