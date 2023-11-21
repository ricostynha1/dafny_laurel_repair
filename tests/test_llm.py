import unittest
import subprocess


class TestsLLM(unittest.TestCase):
    def test_llm_config_path(self):
        self.maxDiff = None
        command = "poetry run python src/test_harness.py --disable_date llm configs/config_llm_test.yaml"

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

        expected_output_file = "./tests/expected_output/test_llm_config_path.txt"
        with open(expected_output_file, "r") as f:
            expected_output = f.read()
            # Remove the \n in the end of the file
            self.assertEqual(result.stderr.strip(), expected_output[:-1])
