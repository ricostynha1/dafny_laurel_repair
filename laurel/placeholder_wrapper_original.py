import logging
import subprocess
import os

PLACEHOLDER_CSHARP_PATH = "placeholder_finder/bin/Debug/net6.0/placeholder_finder"
logger = logging.getLogger(__name__)


def call_placeholder_finder(
    error_message,
    method_file,
    method_name,
    optional_files=None,
    blacklisted_file=None,
    multiple_locations=False,
):
    command = [
        os.path.join(os.path.dirname(__file__), PLACEHOLDER_CSHARP_PATH),
        method_file,
        method_name,
        str(multiple_locations),
    ]
    if optional_files:
        if not os.path.isabs(optional_files):
            optional_files = os.path.abspath(os.path.normpath(optional_files))
        command.append(optional_files)
    if blacklisted_file:
        command.append(blacklisted_file)
    try:
        result = subprocess.run(
            command, input=error_message, capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        logger.error(f"Error in call_placeholder_finder: {str(e.stderr)}")
        logger.error(
            f"Arguments were: method_file={method_file}, method_name={method_name}, optional_files={optional_files}, blacklisted_file={blacklisted_file}"
        )
        return ""
    output = result.stdout.strip()
    print(output)
    return output
