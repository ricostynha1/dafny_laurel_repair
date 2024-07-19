import sys
import shutil
import unittest

sys.path.append("./src")
from src.placeholder_wrapper import call_placeholder_finder


class TestsLLM(unittest.TestCase):
    def test_placeholder_finder_multiple_errors(self):
        error_file = "./tests_package/ressources/LemmaMaxOfConcat_fix_74.dfy_10_0_error"
        method_name = "LemmaMaxOfConcat"
        with open(error_file, "r") as file:
            error_message = file.read()

        new_method_path = "/usr/local/home/eric/dafny_repos/libraries/src/Collections/Sequences/LemmaMaxOfConcat_fix_74.dfy"

        call_placeholder_finder(error_message, new_method_path, method_name)

        self.assertEqual("", "")

    def test_placeholder_finder_multiple_locations(self):
        error_file = "./tests_package/ressources/LemmaSeqPrefixNeq_fix_51.dfy_1_0_error"
        method_file = "./tests_package/ressources/LemmaSeqPrefixNeq_fix_51.dfy"
        result_file = "./tests_package/ressources/LemmaSeqPrefixNeq_fix_51.dfy_output"
        method_name = "LemmaSeqPrefixNeq"
        with open(error_file, "r") as file:
            error_message = file.read()

        # copy method file to "/usr/local/home/eric/dafny_repair/NonlinearArithmetic/"
        new_method_path = "/usr/local/home/eric/dafny_repos/libraries/src/Collections/Sequences/LemmaSeqPrefixNeq_51.dfy"
        shutil.copy(method_file, new_method_path)

        output = call_placeholder_finder(error_message, new_method_path, method_name)
        with open(result_file, "r") as file:
            expected_output = file.read()

        self.assertEqual(output, expected_output)
        # os.remove(new_method_path)

        self.assertEqual("", "")

    def test_placeholder_finder_dependencies(self):
        error_file = "./tests_package/ressources/Sqrt2Exists_fix_27.dfy_1_0_error"
        method_file = "./tests_package/ressources/Sqrt2Exists_fix_27.dfy"
        result_file = "./tests_package/ressources/Sqrt2Exists_fix_27.dfy_output"
        method_name = "Sqrt2Exists"
        with open(error_file, "r") as file:
            error_message = file.read()

        output = call_placeholder_finder(
            error_message,
            method_file,
            method_name,
            optional_files="/usr/local/home/eric/dafny_repos/Dafny-VMC/src/**/*.dfy",
            blacklisted_file="Reals.dfy",
        )

        with open(result_file, "r") as file:
            expected_output = file.read()

        self.assertEqual(output, expected_output)
        self.assertEqual("", "")
