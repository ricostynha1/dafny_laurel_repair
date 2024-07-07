import logging
import os
import shutil
import traceback
import urllib.parse

from config_parsing import parse_config_llm
from dafny_utils import (
    compare_errormessage,
    extract_dafny_functions,
)
from error_parser import remove_warning
from llm_prompt import Llm_prompt
from Method import Method
from utils import (
    extract_string_between_backticks,
    read_pruning_result,
    write_csv_header_arg,
)
from select_example import ExamplesSelector

logger = logging.getLogger(__name__)

# TODO: pass this as a configuration parameter
SERVER_NAME = "http://c10-10.sysnet.ucsd.edu:8866/"


def generate_notebook_url(result_file, assertion_file, method_index):
    query_params = {
        "results": result_file,
        "assertions": assertion_file,
        "method": method_index,
    }

    encoded_params = urllib.parse.urlencode(query_params)

    full_url = SERVER_NAME + "?" + encoded_params
    return full_url


def generate_fix_llm(
    config_file,
    pruning_file,
    output_file=None,
    training_file=None,
    method_to_process=None,
):
    pruning_results = read_pruning_result(pruning_file)
    _, config = parse_config_llm(config_file)
    method_processed, success_count = 0, 0

    header = [
        "Index",
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
        "Prompt Index",
        "Prompt name",
        "Error message",
        "Feedback",
        "Try",
        "Diff",
        "Url",
    ]
    csv_writer, file = write_csv_header_arg(
        output_file if output_file is not None else config["Results_file"], header
    )
    logger.info(
        f"Results file: {output_file if output_file is not None else config['Results_file']}"
    )
    examples_selectors = []
    for config_prompt in config["Prompts"]:
        if training_file is not None:
            print(f"Training file: {training_file}")
            if isinstance(config_prompt["Context"], dict):
                config_prompt["Context"]["Training_file"] = training_file
        examples_selectors.append(ExamplesSelector(config_prompt))
    for row in pruning_results:
        if method_to_process is not None and method_processed != method_to_process:
            method_processed += 1
            continue
        print(f"Method processed: {method_processed}/{len(pruning_results)}")
        (
            method,
            tmp_original_file_location,
            original_method_file,
        ) = setup_verification_environment(config, row, method_processed)
        try:
            notebook_url = generate_notebook_url(
                output_file if output_file is not None else config["Results_file"],
                pruning_file,
                method.index,
            )
            success = process_method_bis(
                method,
                config,
                method_processed,
                row["New Method File"],
                original_method_file,
                csv_writer,
                notebook_url,
                examples_selectors,
            )
            success_count += 1 if success else 0
        except Exception as e:
            traceback_str = traceback.format_exc()
            logger.error(f"An error occurred: {e}\n{traceback_str}")
        cleanup_environment(tmp_original_file_location, row["Original File"])
        logger.info(f"Success rate: {success_count}/{method_processed}")
        method_processed += 1

    file.close()
    return success_count, method_processed


def test_prompt(
    llm_prompt, prompt_path, config, method, index, try_nb, method_with_placeholder
):
    logger.info(f"{method.method_name} ===> Try {try_nb+1}")
    response = llm_prompt.get_fix(
        config["Model_parameters"],
    )
    # TODO this is going to be an assertion
    fix_prompt = response
    print(f"Fix prompt: {fix_prompt}")
    logger.info(fix_prompt)
    # TODO insert the assertion
    if "\n" not in fix_prompt:
        new_method_content = method_with_placeholder.replace(
            "<assertion> Insert assertion here </assertion>", fix_prompt
        )
        print(new_method_content)
    else:
        code = extract_string_between_backticks(fix_prompt)
        new_method_content = get_new_method_content(
            code if code else fix_prompt, method.method_name
        )
    diff = method.get_diff(new_method_content)
    new_method = method.create_modified_method(
        new_method_content, os.path.dirname(method.file_path), try_nb, "fix"
    )
    logger.debug(f"diff : {diff}")
    method.move_to_results_directory(config["Results_dir"])
    new_method.run_verification(config["Results_dir"], config.get("Dafny_args", ""))
    return new_method, diff


def insert_assertion(method_with_placeholder, original_method, fix_prompt, try_number):
    if "\n" not in fix_prompt:
        new_method_content = method_with_placeholder.replace(
            "<assertion> Insert assertion here </assertion>", fix_prompt
        )
    else:
        code = extract_string_between_backticks(fix_prompt)
        new_method_content = get_new_method_content(
            code if code else fix_prompt, original_method.method_name
        )
    diff = original_method.get_diff(new_method_content)
    new_method = original_method.create_modified_method(
        new_method_content,
        os.path.dirname(original_method.file_path),
        try_number,
        "fix",
    )
    logger.debug(f"diff : {diff}")
    return new_method, diff


def process_method_bis(
    method,
    config,
    index,
    original_file_location,
    original_method_file,
    csv_writer,
    notebook_url,
    examples_selectors,
):
    success = False
    logger.info("+--------------------------------------+")
    method.run_verification(config["Results_dir"], config.get("Dafny_args", ""))
    logger.debug(method)
    new_method = None
    diff = ""
    for prompt_index, config_prompt in enumerate(config["Prompts"], start=1):
        # create a new prompt
        threshold = 0
        if (
            config_prompt["Context"] is not None
            and "Threshold" in config_prompt["Context"]
        ):
            threshold = config_prompt["Context"]["Threshold"]

        llm_prompt = Llm_prompt(
            config_prompt["System_prompt"],
            examples_selectors[prompt_index - 1],
        )
        prompt_path = f"{method.file_path}_{index}_{prompt_index}_{config_prompt['Prompt_name']}_prompt"
        llm_prompt.set_path(prompt_path)
        method_with_placeholder = llm_prompt.add_question(
            method.file_path,
            method.method_name,
            method.entire_error_message,
            config["Model_parameters"],
            config_prompt,
            method.entire_error_message if config_prompt["Feedback"] else None,
            examples_selectors[prompt_index - 1],
            threshold,
        )
        new_prompts = llm_prompt.get_n_fixes(
            config["Model_parameters"], config_prompt["Nb_tries"]
        )
        for i, prompt in enumerate(new_prompts, start=1):
            try:
                logger.info(f"{method.method_name} ===> Try {i}")
                feedback = False
                prompt_path = f"{method.file_path}_{index}_{prompt_index}_{config_prompt['Prompt_name']}_prompt"
                prompt.set_path(prompt_path)
                response = prompt.get_latest_message()["content"]
                new_method, diff = insert_assertion(
                    method_with_placeholder, method, response, i
                )
                method.move_to_results_directory(config["Results_dir"])
                new_method.run_verification(
                    config["Results_dir"], config.get("Dafny_args", "")
                )
                prompt.save_prompt()
                prompt_length = llm_prompt.get_prompt_length(
                    config["Model_parameters"]["Encoding"]
                )
                logger.info(f"Prompt length: {prompt_length}")
                if new_method.verification_result == "Correct":
                    logger.info(f"Success with prompt {prompt_index} on try {i}")
                    success = True

                method.move_to_results_directory(os.path.dirname(original_method_file))
                new_method.move_to_results_directory(config["Results_dir"])
                store_results(
                    method,
                    new_method,
                    original_file_location,
                    prompt_path,
                    prompt_length,
                    prompt_index,
                    config_prompt["Prompt_name"],
                    "",
                    feedback,
                    i,
                    diff,
                    notebook_url,
                    csv_writer,
                )
                previous_error = remove_warning(method.entire_error_message)
                new_error = ""
                if new_method.entire_error_message is not None:
                    new_error = remove_warning(new_method.entire_error_message)
                if (
                    not compare_errormessage(previous_error, new_error)
                    and config_prompt["Error_feedback"]
                ):
                    logger.info(f"Try feedback with prompt {prompt_index} ")
                    feedback = True
                    method.file_path = original_method_file

                    prompt.feedback_error_message(new_error)
                    prompt.get_fix(config["Model_parameters"])
                    response = prompt.get_latest_message()["content"]
                    new_method, diff = insert_assertion(
                        method_with_placeholder, method, response, i
                    )
                    method.move_to_results_directory(config["Results_dir"])
                    new_method.run_verification(
                        config["Results_dir"], config.get("Dafny_args", "")
                    )
                    prompt.save_prompt()
                    prompt_length = prompt.get_prompt_length(
                        config["Model_parameters"]["Encoding"]
                    )
                    logger.info(f"Prompt length: {prompt_length}")
                    method.move_to_results_directory(
                        os.path.dirname(original_method_file)
                    )
                    if new_method.verification_result == "Correct":
                        logger.info(f"Success with prompt {prompt_index} on try {i}")
                        success = True
                    # TODO: gather prompt things in the same object
                    store_results(
                        method,
                        new_method,
                        original_file_location,
                        prompt_path,
                        prompt_length,
                        prompt_index,
                        config_prompt["Prompt_name"],
                        "",
                        feedback,
                        i,
                        diff,
                        notebook_url,
                        csv_writer,
                    )
                    new_method.move_to_results_directory(config["Results_dir"])

            except Exception as e:
                traceback_str = traceback.format_exc()
                logger.error(f"An error occurred: {e}\n{traceback_str}")
                prompt.save_prompt()
                prompt_length = prompt.get_prompt_length(
                    config["Model_parameters"]["Encoding"]
                )
                error_path = f"{method.file_path}_{index}_{prompt_index}_error"
                with open(error_path, "w") as f:
                    f.write(f"{e}\n{traceback_str}")
                store_results(
                    method,
                    new_method,
                    original_file_location,
                    prompt_path,
                    prompt_length,
                    prompt_index,
                    config_prompt["Prompt_name"],
                    error_path,
                    feedback,
                    i,
                    diff,
                    notebook_url,
                    csv_writer,
                )
    return success


def process_method(
    method,
    config,
    index,
    original_file_location,
    original_method_file,
    csv_writer,
    notebook_url,
    examples_selectors,
):
    logger.info("+--------------------------------------+")
    method.run_verification(config["Results_dir"], config.get("Dafny_args", ""))
    logger.debug(method)
    new_method = None
    diff = ""
    for prompt_index, config_prompt in enumerate(config["Prompts"], start=1):
        for i in range(config_prompt["Nb_tries"]):
            feedback = False

            threshold = 0
            if (
                config_prompt["Context"] is not None
                and "Threshold" in config_prompt["Context"]
            ):
                threshold = config_prompt["Context"]["Threshold"]

            try:
                llm_prompt = Llm_prompt(
                    config_prompt["System_prompt"],
                    examples_selectors[prompt_index - 1],
                )
                prompt_path = f"{method.file_path}_{index}_{i}_{config_prompt['Prompt_name']}_prompt"
                method_with_placeholder = llm_prompt.add_question(
                    method.file_path,
                    method.method_name,
                    method.entire_error_message,
                    config["Model_parameters"],
                    config_prompt,
                    method.entire_error_message if config_prompt["Feedback"] else None,
                    examples_selectors[prompt_index - 1],
                    threshold,
                )
                new_method, diff = test_prompt(
                    llm_prompt,
                    prompt_path,
                    config,
                    method,
                    index,
                    i,
                    method_with_placeholder,
                )
                llm_prompt.save_prompt(prompt_path)
                prompt_length = llm_prompt.get_prompt_length(
                    config["Model_parameters"]["Encoding"]
                )
                logger.info(f"Prompt length: {prompt_length}")
                previous_error = remove_warning(method.entire_error_message)
                new_error = ""
                if new_method.entire_error_message is not None:
                    new_error = remove_warning(new_method.entire_error_message)
                if new_method.verification_result == "Correct":
                    logger.info(f"Success with prompt {prompt_index} on try {i}")
                    method.move_to_results_directory(
                        os.path.dirname(original_file_location)
                    )
                    new_method.move_to_results_directory(config["Results_dir"])
                    store_results(
                        method,
                        new_method,
                        original_file_location,
                        prompt_path,
                        prompt_length,
                        prompt_index,
                        config_prompt["Prompt_name"],
                        "",
                        feedback,
                        i,
                        diff,
                        notebook_url,
                        csv_writer,
                    )
                    return (
                        new_method,
                        prompt_path,
                        prompt_length,
                        diff,
                        prompt_index,
                        config_prompt["Prompt_name"],
                        True,
                    )
                elif (
                    not compare_errormessage(previous_error, new_error)
                    and config_prompt["Error_feedback"]
                ):
                    feedback = True
                    new_method.move_to_results_directory(config["Results_dir"])
                    # shutil.copy(original_file_location, original_method_file)
                    shutil.copy(method.file_path, original_method_file)
                    method.file_path = original_method_file

                    llm_prompt.feedback_error_message(new_error)
                    new_method, diff = test_prompt(
                        llm_prompt,
                        prompt_path,
                        config,
                        method,
                        index,
                        i,
                        method_with_placeholder,
                    )
                    llm_prompt.save_prompt(prompt_path)
                    prompt_length = llm_prompt.get_prompt_length(
                        config["Model_parameters"]["Encoding"]
                    )
                    logger.info(f"Prompt length: {prompt_length}")
                    if new_method.verification_result == "Correct":
                        method.move_to_results_directory(
                            os.path.dirname(original_file_location)
                        )
                        new_method.move_to_results_directory(config["Results_dir"])
                        store_results(
                            method,
                            new_method,
                            original_file_location,
                            prompt_path,
                            prompt_length,
                            prompt_index,
                            config_prompt["Prompt_name"],
                            "",
                            feedback,
                            i,
                            diff,
                            notebook_url,
                            csv_writer,
                        )
                        logger.info(f"Success with prompt {prompt_index} on try {i}")
                        return (
                            new_method,
                            prompt_path,
                            prompt_length,
                            diff,
                            prompt_index,
                            config_prompt["Prompt_name"],
                            True,
                        )
                if i + 1 != config_prompt["Nb_tries"]:
                    # method.move_to_results_directory(
                    #     os.path.dirname(original_method_file)
                    # )
                    new_method.move_to_results_directory(config["Results_dir"])
                    store_results(
                        method,
                        new_method,
                        original_file_location,
                        prompt_path,
                        prompt_length,
                        prompt_index,
                        config_prompt["Prompt_name"],
                        "",
                        feedback,
                        i,
                        diff,
                        notebook_url,
                        csv_writer,
                    )
                    method.move_to_results_directory(
                        os.path.dirname(original_method_file)
                    )
                    # shutil.copy(method.file_path, original_file_location)
                    # method.file_path = original_file_location
                else:
                    store_results(
                        method,
                        new_method,
                        original_file_location,
                        prompt_path,
                        prompt_length,
                        prompt_index,
                        config_prompt["Prompt_name"],
                        "",
                        feedback,
                        i,
                        diff,
                        notebook_url,
                        csv_writer,
                    )

            except Exception as e:
                traceback_str = traceback.format_exc()
                logger.error(f"An error occurred: {e}\n{traceback_str}")
                llm_prompt.save_prompt(prompt_path)
                prompt_length = llm_prompt.get_prompt_length(
                    config["Model_parameters"]["Encoding"]
                )
                error_path = f"{method.file_path}_{index}_{i}_error"
                with open(error_path, "w") as f:
                    f.write(f"{e}\n{traceback_str}")
                store_results(
                    method,
                    new_method,
                    original_file_location,
                    prompt_path,
                    prompt_length,
                    prompt_index,
                    config_prompt["Prompt_name"],
                    error_path,
                    feedback,
                    i,
                    diff,
                    notebook_url,
                    csv_writer,
                )

        method.move_to_results_directory(os.path.dirname(original_file_location))
        if new_method is not None:
            new_method.move_to_results_directory(config["Results_dir"])
        return (
            new_method,
            prompt_path,
            prompt_length,
            diff,
            prompt_index,
            config_prompt["Prompt_name"],
            False,
        )


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
        original_method_file,
    )


def get_new_method_content(fix_prompt, method_name):
    new_method_content = extract_dafny_functions(fix_prompt, method_name)
    new_method_content = "\n".join(
        line.lstrip("+") for line in new_method_content.splitlines()
    )
    return new_method_content


def cleanup_environment(tmp_original_file_location, original_file_path):
    shutil.copy(tmp_original_file_location, original_file_path)


def store_results(
    method,
    new_method,
    original_file,
    prompt_path,
    prompt_length,
    prompt_index,
    prompt_name,
    error_message_file,
    feedback,
    try_number,
    diff,
    notebook_url,
    csv_writer,
):
    fix_stats = []

    try:
        fix_stats.extend(
            [
                method.index,
                original_file,
                method.method_name,
                method.verification_time,
                method.verification_result,
                method.dafny_log_file,
                method.error_message,
                method.error_file_path,
            ]
        )
    except AttributeError as e:
        logger.info(f"An error occurred when writing the results: {e}")
        fix_stats.extend(
            [
                "default_method_name",
                "default_verification_time",
                "Exception",
                "default_dafny_log_file",
                "default_error_message",
                "default_error_file_path",
            ]
        )

    try:
        fix_stats.extend(
            [
                new_method.file_path,
                new_method.method_name,
                new_method.verification_time,
                new_method.verification_result,
                new_method.dafny_log_file,
                new_method.error_message,
                new_method.error_file_path,
            ]
        )
    except (AttributeError, NameError):
        fix_stats.extend(
            [
                "default_file_path",
                "default_method_name",
                "default_verification_time",
                "default_verification_result",
                "default_dafny_log_file",
                "default_error_message",
                "default_error_file_path",
            ]
        )

    fix_stats.extend(
        [
            prompt_path,
            prompt_length,
            prompt_index,
            prompt_name,
            error_message_file,
            feedback,
            try_number,
            diff if len(diff) > 5 else "",
            notebook_url,
        ]
    )
    if csv_writer:
        csv_writer.writerow(fix_stats)
