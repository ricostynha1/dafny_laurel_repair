import argparse
import os
import subprocess
import yaml


def parse_config(config_file):
    with open(config_file, "r") as stream:
        try:
            config_data = yaml.safe_load(stream)
            results_dir = config_data.get("results_dir")
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            methods_data = config_data.get("methods", [])

            methods_list = []
            for method_data in methods_data:
                file_path = method_data.get("file_path")
                method_name = method_data.get("method_name")

                if file_path and method_name:
                    method = Method(file_path, method_name)
                    methods_list.append(method)

            return results_dir, methods_list
        except yaml.YAMLError as exc:
            print(exc)


class Method:
    def __init__(self, file_path, method_name):
        self.file_path = file_path
        self.method_name = method_name
        self.verification_time = None
        self.verification_result = None
        self.error_message = None
        self.dafny_log_file = None

    def parse_verification_outcome(self):
        pass

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

            self.verification_time = 0
            self.verification_result = True

            print(f"Verification successful for method '{self.method_name}'.")
        except subprocess.CalledProcessError as e:
            self.error_message = e.stdout
            self.verification_result = False

    def __str__(self):
        return f"Method: {self.method_name}\nVerification time: {self.verification_time} seconds\nVerification result: {self.verification_result}"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run Dafny verification for specified methods."
    )
    parser.add_argument("config_file", help="Path to the YAML config file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    results_dir, methods = parse_config(args.config_file)

    for method in methods:
        method.run_verification(results_dir)
