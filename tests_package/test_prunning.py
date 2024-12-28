import unittest
import subprocess


class TestsPruning(unittest.TestCase):
    def test_tool_output(self):
        # Define your tool command with specific arguments
        command = "poetry run python laurel/laurel_main.py --disable_date prune-assert configs/config_pruning_test.yaml"

        # Run the command and capture the output
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                shell=True,
                executable="/usr/bin/zsh",
            )
        except subprocess.CalledProcessError as e:
            self.error_message = e.stdout
            if e.stderr:
                print(e.stderr)
            if e.stdout:
                print(e.stdout)

        expected_output_file = "./tests_package/expected_output/test_pruning_tool.txt"
        with open(expected_output_file, "r") as f:
            expected_output = f.read()
            # Remove the \n in the end of the file
            self.maxDiff = None
            self.assertEqual(result.stderr.strip(), expected_output[:-1])
