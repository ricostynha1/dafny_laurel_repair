import logging
import os
import shutil
import traceback
from llm_prompt import Llm_prompt
from dafny_utils import (
    extract_dafny_functions,
)
from config_parsing import parse_config_llm
from utils import write_csv_header_arg, extract_string_between_backticks

from Method import Method

logger = logging.getLogger(__name__)


def generate_fix_llm(config_file, pruning_results=None):
    if pruning_results:
        return handle_pruning_results(pruning_results, config_file)
    else:
        return handle_no_pruning_results(config_file)


def handle_pruning_results(pruning_results, config_file):
    _, config = parse_config_llm(config_file)
    method_processed, success_count = 0, 0

    header = [
        "Original Method File",
        "Original Method",
        "Original Method Time",
        "Original Method Result",
        "Original Result File",
        "Original Error Message",
        "Original Error Message File",
        "New Method File",
        "New Method",
        "New Method Time",
        "New Method Result",
        "New Method Result File",
        "New Method Error Message",
        "New Method Error Message File",
        "Prompt File",
        "Prompt Length",
        "Diff",
    ]
    csv_writer = write_csv_header_arg(config["Results_file"], header)
    for row in pruning_results:
        method_processed += 1
        # if method_processed > 1:
        #     break
        method, tmp_original_file_location = setup_verification_environment(
            config, row, method_processed
        )
        try:
            new_method, prompt_path, prompt_length, diff = process_method(
                method, config, method_processed
            )
            success_count += (
                1
                if store_results_and_compare(
                    method,
                    new_method,
                    config,
                    row["New Method File"],
                    prompt_path,
                    prompt_length,
                    diff,
                    csv_writer=csv_writer,
                )
                else 0
            )
        except Exception as e:
            traceback_str = traceback.format_exc()
            logger.error(f"An error occurred: {e}\n{traceback_str}")
        cleanup_environment(tmp_original_file_location, row["Original File"])
        logger.info(f"Success rate: {success_count}/{method_processed}")

    return success_count, method_processed


def handle_no_pruning_results(config_file):
    methods, config = parse_config_llm(config_file)
    method_processed, success_count = 0, 0

    for method in methods:
        original_file_location = method.file_path
        method_processed += 1
        new_method, prompt_path, prompt_length, diff = process_method(
            method, config, method_processed
        )
        success_count += (
            1
            if store_results_and_compare(
                method,
                new_method,
                config,
                method.file_path,
                prompt_path,
                prompt_length,
                diff,
            )
            else 0
        )
        shutil.copy(method.file_path, original_file_location)
        logger.info(f"Success rate: {success_count}/{method_processed}")

    return success_count, method_processed


def process_method(method, config, index):
    logger.info("+--------------------------------------+")
    method.run_verification(config["Results_dir"], config.get("Dafny_args", ""))
    logger.debug(method)
    try:
        llm_prompt = Llm_prompt(
            config["Prompt"]["System_prompt"], config["Prompt"]["Context"]
        )
        llm_prompt.add_question(
            method.file_path,
            method.method_name,
            config["Prompt"]["Fix_prompt"],
            config["Model_parameters"],
            config["Prompt"]["Method_context"],
            method.entire_error_message if config["Prompt"]["Feedback"] else None,
        )
        prompt_path = f"{method.file_path}_{index}_prompt"
        llm_prompt.save_prompt(prompt_path)
        prompt_length = llm_prompt.get_prompt_length(
            config["Model_parameters"]["Encoding"]
        )
        logger.info(f"Prompt length: {prompt_length}")

        response = llm_prompt.generate_fix(
            config["Model_parameters"],
        )
        fix_prompt = response["choices"][0]["message"]["content"]
        logger.info(fix_prompt)
        code = extract_string_between_backticks(fix_prompt)
        new_method_content = get_new_method_content(
            code if code else fix_prompt, method.method_name
        )
        diff = method.get_diff(new_method_content)
        new_method = method.create_modified_method(
            new_method_content, os.path.dirname(method.file_path), index, "fix"
        )
        logger.debug(f"diff : {diff}")
        method.move_to_results_directory(config["Results_dir"])
        new_method.run_verification(config["Results_dir"], config.get("Dafny_args", ""))
        return new_method, prompt_path, prompt_length, diff
    except Exception as e:
        method.move_to_results_directory(config["Results_dir"])
        traceback_str = traceback.format_exc()
        logger.error(f"An error occurred: {e}\n{traceback_str}")


def setup_verification_environment(config, row, index=0):
    original_filepath = row["Original File"]
    tmp_original_file_location = shutil.move(
        original_filepath,
        os.path.join(config["Results_dir"], os.path.basename(original_filepath)),
    )
    original_method_file = os.path.join(
        os.path.dirname(original_filepath), os.path.basename(row["New Method File"])
    )
    if row["New Method File"] != original_method_file:
        shutil.copy(
            row["New Method File"],
            # os.path.join(config["Results_dir"], os.path.basename(row["New Method File"])),
            original_method_file,
        )
    return (
        Method(original_method_file, row["Original Method"], index=index),
        tmp_original_file_location,
    )


def get_new_method_content(fix_prompt, method_name):
    new_method_content = extract_dafny_functions(fix_prompt, method_name)
    new_method_content = "\n".join(
        line.lstrip("+") for line in new_method_content.splitlines()
    )
    return new_method_content


def cleanup_environment(tmp_original_file_location, original_file_path):
    shutil.copy(tmp_original_file_location, original_file_path)


def store_results_and_compare(
    method,
    new_method,
    config,
    original_file,
    prompt_path,
    prompt_length,
    diff,
    csv_writer=None,
):
    comparison_result, comparison_details = method.compare(new_method)
    new_method.move_to_results_directory(config["Results_dir"])
    logger.info(comparison_details)
    fix_stats = [
        original_file,
        method.method_name,
        method.verification_time,
        method.verification_result,
        method.dafny_log_file,
        method.error_message,
        method.error_file_path,
        new_method.file_path,
        new_method.method_name,
        new_method.verification_time,
        new_method.verification_result,
        new_method.dafny_log_file,
        new_method.error_message,
        new_method.error_file_path,
        prompt_path,
        prompt_length,
        diff if len(diff) > 5 else "",
    ]
    if csv_writer:
        csv_writer.writerow(fix_stats)
    return comparison_result
