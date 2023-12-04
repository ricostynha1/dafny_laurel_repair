import logging
import os
import time
import traceback

from dafny_utils import (
    extract_assertions,
    extract_method_and_lemma_names,
    count_dfy_files,
    get_dfy_files,
)
from utils import write_csv_header
from config_parsing import parse_config_assert_pruning

from Method import Method

logger = logging.getLogger(__name__)


def remove_assertions(config_file):
    config = parse_config_assert_pruning(config_file)
    project_path = config["Project_path"]
    results_path = config["Results_dir"]
    stats_file = config["Stats_file"]

    total_files = count_dfy_files(project_path)
    file_counter = 0
    start_time = time.time()
    assertion_index = [0]

    stats = []
    csv_writer = write_csv_header(stats_file)

    for file_path in get_dfy_files(project_path):
        file_counter += 1
        file_location = os.path.dirname(file_path)
        logger.info(f"Starting file {file_counter}/{total_files}:{file_path}")

        try:
            process_file(
                file_path,
                file_location,
                results_path,
                config,
                csv_writer,
                stats,
                assertion_index,
            )
        except Exception as e:
            traceback_str = traceback.format_exc()
            logger.error(f"An error occurred: {e}\n{traceback_str}")

        elapsed_time = time.time() - start_time
        logger.info(
            f"==== Finished file {file_path} {file_counter}/{total_files} ====="
        )
        logger.debug(f"Elapsed time: {elapsed_time}")


def process_file(
    file_path, file_location, results_path, config, csv_writer, stats, assertion_index
):
    try:
        with open(file_path) as file:
            content = file.read()
        method_list, success = process_methods(file_path, content, results_path, config)

        if success:
            sorted_methods = sorted(method_list, key=lambda x: x.verification_time)
            for method in sorted_methods:
                process_method(
                    method,
                    file_location,
                    results_path,
                    config,
                    csv_writer,
                    stats,
                    assertion_index,
                )

    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"An error occurred: {e}\n{traceback_str}")


def process_methods(file_path, content, results_path, config):
    method_names = extract_method_and_lemma_names(content)
    method_list = []
    success = True

    for method_name in method_names:
        try:
            method = Method(file_path, method_name)
            method_list.append(method)
            success = method.run_verification(
                results_path, additionnal_args=config["Dafny_args"]
            )

            if not success:
                method.verification_time = 0
                continue

        except Exception as e:
            traceback_str = traceback.format_exc()
            logger.error(f"An error occurred: {e}\n{traceback_str}")
            continue

    return method_list, success


def process_method(
    method, file_location, results_path, config, csv_writer, stats, assertion_index
):
    try:
        file_content = method.get_file_content()
        assertions = extract_assertions(method.get_method_content(file_content))

        for assertion in assertions:
            assertion_index[0] += 1
            logger.info(
                f"Starting assertion {assertions.index(assertion) + 1}/{len(assertions)} for {method.method_name}"
            )
            process_assertion(
                method,
                assertion,
                file_location,
                results_path,
                config,
                csv_writer,
                stats,
                file_content,
                assertion_index,
            )

    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"An error occurred: {e}\n{traceback_str}")


def process_assertion(
    method,
    assertion,
    file_location,
    results_path,
    config,
    csv_writer,
    stats,
    file_content,
    assertion_index,
):
    method_index = assertion_index[0]

    try:
        modified_method = method.get_method_content(file_content).replace(
            assertion, "", 1
        )
        new_method = method.create_modified_method(
            modified_method, file_location, method_index, "prunned"
        )
        logger.info(
            f"Creating modified method for {method.method_name} in {new_method.file_path}"
        )

        process_verification(
            new_method, method, results_path, config, csv_writer, stats, assertion
        )

    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"An error occurred: {e}\n{traceback_str}")
        new_method.move_to_results_directory(results_path)


def process_verification(
    new_method, method, results_path, config, csv_writer, stats, assertion
):
    try:
        method.move_original(results_path)
        success = new_method.run_verification(
            results_path, additionnal_args=config["Dafny_args"]
        )
        method.move_back()

        if not success:
            new_method.move_to_results_directory(results_path)
            return

        time_difference = float("nan")
        if new_method.verification_result == "Correct":
            time_difference = method.verification_time - new_method.verification_time

        assertions_stats = [
            new_method.index,
            method.file_path,
            method.method_name,
            method.verification_time,
            method.verification_result,
            method.dafny_log_file,
            assertion,
            time_difference,
            new_method.file_path,
            new_method.method_name,
            new_method.verification_time,
            new_method.verification_result,
            new_method.dafny_log_file,
        ]

        logger.debug(new_method)
        stats.append(assertions_stats)
        logger.debug(f"Writing stats: {assertions_stats}")
        csv_writer.writerow(assertions_stats)
        new_method.move_to_results_directory(results_path)

    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"An error occurred: {e}\n{traceback_str}")
        new_method.move_to_results_directory(results_path)
        method.move_back()
