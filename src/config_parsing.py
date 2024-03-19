import logging
import os
import traceback
import yaml
from Method import Method

logger = logging.getLogger(__name__)


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
            traceback_str = traceback.format_exc()
            logger.error(f"{exc}\n{traceback_str}")
