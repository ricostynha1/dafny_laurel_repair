import subprocess
import os

PLACEHOLDER_CSHARP_PATH = "placeholder_finder/bin/Debug/net6.0/placeholder_finder"


def call_placeholder_finder(
    error_message, method_file, method_name, optional_files=None, blacklisted_file=None
):
    command = [
        os.path.join(os.path.dirname(__file__), PLACEHOLDER_CSHARP_PATH),
        method_file,
        method_name,
    ]
    if optional_files:
        command.append(optional_files)
    if blacklisted_file:
        command.append(blacklisted_file)
    try:
        result = subprocess.run(
            command, input=error_message, capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print("Error: ", e.stderr)
        print("Output: ", e.stdout)
        return ""
    output = result.stdout.strip()
    print(output)
    return output
