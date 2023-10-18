import argparse
import subprocess


class Method:
    def __init__(self, file_path, method_name):
        self.file_path = file_path
        self.method_name = method_name
        self.verification_time = None
        self.verification_result = None
        self.error_message = None

    def run_verification(self):
        # TODO changne the log file name a result directory
        dafny_command = [
            "dafny",
            "verify",
            "--boogie-filter",
            f"*{self.method_name}*",
            "--log-format",
            f"text;LogFileName={self.method_name}",
            self.file_path,
        ]

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
    parser.add_argument("file_path", help="Path to the Dafny file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    # TODO need to change to a config file where methods are defined per file
    method_names = ["UnitIsUnique"]

    methods = [Method(args.file_path, method_name) for method_name in method_names]

    for method in methods:
        method.run_verification()

    for method in methods:
        print(method)
