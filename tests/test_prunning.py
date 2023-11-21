import unittest
import subprocess


class TestsPruning(unittest.TestCase):
    def test_tool_output(self):
        # Define your tool command with specific arguments
        command = ""

        # Run the command and capture the output
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            self.error_message = e.stdout
            if e.stderr:
                print(e.stderr)
            if e.stdout:
                print(e.stdout)

        # Check if the return code is 0 (success)
        self.assertEqual(result.returncode, 0)

        # Check if the output matches your expectations
        expected_output = ""
        self.assertEqual(result.stderr.strip(), expected_output)
