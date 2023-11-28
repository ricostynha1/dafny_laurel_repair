import datetime
import logging
import os
import shutil
import subprocess
from dafny_utils import parse_assertion_results, replace_method, extract_dafny_functions
from utils import adjust_microseconds

logger = logging.getLogger(__name__)


class Method:
    def __init__(self, file_path, method_name, index=0, new_file_path=None):
        if new_file_path:
            shutil.copy(file_path, new_file_path)
            self.file_path = new_file_path
        else:
            self.file_path = file_path
        self.moved_path = None
        self.method_name = method_name
        self.verification_time = None
        self.verification_result = None
        self.error_message = None
        self.dafny_log_file = None
        self.index = index

    def move_original(self, directory):
        file_name, file_extension = os.path.splitext(os.path.basename(self.file_path))
        new_file_path = os.path.join(
            directory, f"{file_name}_original.{file_extension}"
        )
        shutil.move(self.file_path, new_file_path)
        self.moved_path = new_file_path
        logger.debug(
            f"Copied method: {self.method_name} from {self.file_path} to {new_file_path}"
        )

    def move_back(self):
        file_name, file_extension = os.path.splitext(os.path.basename(self.file_path))
        if self.moved_path and os.path.exists(self.moved_path):
            shutil.move(self.moved_path, self.file_path)
            logger.debug(
                f"Move method: {self.method_name} from {self.moved_path} to {self.file_path}"
            )
        else:
            logger.debug(f"File {self.moved_path} does not exist")

    def move_to_results_directory(self, result_directory):
        if not os.path.exists(result_directory):
            os.makedirs(result_directory)

        file_name, file_extension = os.path.splitext(os.path.basename(self.file_path))
        new_file_path = os.path.join(result_directory, f"{file_name}.{file_extension}")
        if os.path.exists(self.file_path):
            shutil.move(self.file_path, new_file_path)
            logger.debug(
                f"Moved method: {self.method_name} from {self.file_path} to {new_file_path}"
            )
            return new_file_path
        else:
            logger.debug(f"File {self.file_path} does not exist")

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
        if (
            new_method.verification_result == "Correct"
            and not self.verification_result == "Correct"
        ):
            return True, "SUCCESS: Second method verifies, and the first one does not."

        if (
            self.verification_result == "Correct"
            and new_method.verification_result == "Correct"
        ):
            if new_method.verification_time < self.verification_time:
                return (
                    True,
                    "SUCCESS: Second method verifies faster than the first one.",
                )
            else:
                return (
                    False,
                    "FAILURE: Second method verifies slower than the first one.",
                )

        return False, "FAILURE: Second method does not verify."

    def run_verification(self, results_directory, additionnal_args=None):
        dafny_command = [
            "dafny",
            "verify",
            "--boogie-filter",
            f'"*{self.method_name}*"',
            "--log-format",
            f'"text;LogFileName={results_directory}/{self.method_name}.txt"',
            self.file_path,
        ]
        dafny_command[-1:-1] = additionnal_args.split() if additionnal_args else []
        logger.debug(dafny_command)

        self.dafny_log_file = f"{results_directory}/{self.method_name}.txt"

        try:
            result = subprocess.run(
                " ".join(dafny_command),
                check=True,
                capture_output=True,
                text=True,
                shell=True,
                executable="/usr/bin/zsh",
            )
            logger.debug(result.stdout)
        except subprocess.CalledProcessError as e:
            self.error_message = e.stdout
            if e.stderr:
                logger.error(e.stderr)
            if e.stdout:
                logger.error(e.stdout)
        self.verification_outcome = parse_assertion_results(self.dafny_log_file)
        if not self.verification_outcome:
            return False
        self.verification_result = (
            # self.verification_outcome[0]["overall_outcome"] == "Correct"
            self.verification_outcome[0]["overall_outcome"]
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
