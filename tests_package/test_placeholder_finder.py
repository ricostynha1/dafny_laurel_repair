import sys
import unittest

sys.path.append("./src")
from src.placeholder_wrapper import call_placeholder_finder


class TestsLLM(unittest.TestCase):
    def test_placeholder_finder_multiple_errors(self):
        error_file = "./tests_package/ressources/LemmaMaxOfConcat_fix_74.dfy_10_0_error"
        method_file = "./tests_package/ressources/LemmaMaxOfConcat_fix_74.dfy"
        method_name = "LemmaMaxOfConcat"
        with open(error_file, "r") as file:
            error_message = file.read()

        call_placeholder_finder(error_message, method_file, method_name)

        self.assertEqual("", "")

    def test_placeholder_finder_multiple_locations(self):
        error_file = "./tests_package/ressources/LemmaSeqPrefixNeq_fix_51.dfy_1_0_error"
        method_file = "./tests_package/ressources/LemmaSeqPrefixNeq_fix_51.dfy"
        method_name = "LemmaSeqPrefixNeq"
        with open(error_file, "r") as file:
            error_message = file.read()

        call_placeholder_finder(error_message, method_file, method_name)

        self.assertEqual("", "")

    def test_placeholder_finder_dependencies(self):
        error_file = "./tests_package/ressources/Sqrt2Exists_fix_27.dfy_1_0_error"
        method_file = "./tests_package/ressources/Sqrt2Exists_fix_27.dfy"
        method_name = "Sqrt2Exists"
        with open(error_file, "r") as file:
            error_message = file.read()

        call_placeholder_finder(error_message, method_file, method_name)

        self.assertEqual("", "")
