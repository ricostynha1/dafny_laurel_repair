import logging
import os
import shutil
import traceback
from llm_prompt import Llm_prompt
from dafny_utils import (
    extract_dafny_functions,
)
from config_parsing import parse_config_llm

from Method import Method

logger = logging.getLogger(__name__)


def generate_fix_llm(config_file, pruning_results=None):
    if pruning_results:
        return handle_pruning_results(pruning_results, config_file)
    else:
        return handle_no_pruning_results(config_file)


def handle_pruning_results(pruning_results, config_file):
    _, config = parse_config_llm(config_file)
    llm_prompt = Llm_prompt(
        config["Prompt"]["System_prompt"], config["Prompt"]["Context"]
    )
    method_processed, success_count = 0, 0
    new_file_location = None

    for row in pruning_results:
        method_processed += 1
        method, new_file_location = setup_verification_environment(config, row)
        new_method = process_method(llm_prompt, method, config)
        success_count += (
            1 if store_results_and_compare(method, new_method, config) else 0
        )
        cleanup_environment(new_file_location, row["File"])
        logger.info(f"Success rate: {success_count}/{method_processed}")

    return success_count, method_processed


def handle_no_pruning_results(config_file):
    methods, config = parse_config_llm(config_file)
    llm_prompt = Llm_prompt(
        config["Prompt"]["System_prompt"], config["Prompt"]["Context"]
    )
    method_processed, success_count = 0, 0

    for method in methods:
        method_processed += 1
        new_method = process_method(llm_prompt, method, config)
        success_count += (
            1 if store_results_and_compare(method, new_method, config) else 0
        )
        logger.info(f"Success rate: {success_count}/{method_processed}")

    return success_count, method_processed


def process_method(llm_prompt, method, config):
    logger.info("+--------------------------------------+")
    method.run_verification(config["Results_dir"], *config.get("Dafny_args", []))
    logger.debug(method)
    try:
        response = llm_prompt.generate_fix(
            method.file_path,
            method.method_name,
            config["Prompt"]["Fix_prompt"],
            config["Model_parameters"],
        )
        fix_prompt = response["choices"][0]["message"]["content"]
        new_method_content = get_new_method_content(fix_prompt, method.method_name)
        new_method = method.create_modified_method(
            new_method_content, os.path.dirname(method.file_path), 0
        )
        new_method.run_verification(
            config["Results_dir"], *config.get("Dafny_args", [])
        )
        return new_method
    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"An error occurred: {e}\n{traceback_str}")


def setup_verification_environment(config, row):
    original_filepath = row["File"]
    new_file_location = shutil.move(
        original_filepath,
        os.path.join(config["Results_dir"], os.path.basename(original_filepath)),
    )
    shutil.copy(
        os.path.join(config["Results_dir"], os.path.basename(row["File new method"])),
        original_filepath,
    )
    return Method(row["File new method"], row["Method"]), new_file_location


def get_new_method_content(fix_prompt, method_name):
    new_method_content = extract_dafny_functions(fix_prompt, method_name)
    new_method_content = "\n".join(
        line.lstrip("+") for line in new_method_content.splitlines()
    )
    return new_method_content


def cleanup_environment(new_file_location, original_file_path):
    shutil.copy(new_file_location, original_file_path)


def store_results_and_compare(method, new_method, config):
    comparison_result, comparison_details = method.compare(new_method)
    new_method.move_to_results_directory(config["Results_dir"])
    logger.info(comparison_details)
    return comparison_result
