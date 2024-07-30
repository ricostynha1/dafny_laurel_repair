import os
import sys
import shutil
import unittest

sys.path.append("./src")
from src.placeholder_wrapper import call_placeholder_finder


class TestsLLM(unittest.TestCase):
    def test_placeholder_finder_multiple_errors(self):
        error_file = "./tests_package/ressources/LemmaMaxOfConcat_fix_74.dfy_10_0_error"
        result_file = "./tests_package/ressources/LemmaMaxOfConcat_fix_74.dfy_output"
        method_file = "./tests_package/ressources/LemmaMaxOfConcat_fix_74.dfy"
        method_name = "LemmaMaxOfConcat"
        with open(error_file, "r") as file:
            error_message = file.read()

        new_method_path = "/usr/local/home/eric/dafny_repos/libraries/src/Collections/Sequences/LemmaMaxOfConcat_fix_74.dfy"
        shutil.copy(method_file, new_method_path)

        try:
            output = call_placeholder_finder(
                error_message, new_method_path, method_name
            )
        except Exception as e:
            print(e)
        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(expected_output, output)

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

        try:
            output = call_placeholder_finder(
                error_message, new_method_path, method_name
            )
        except Exception as e:
            print(e)
        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(output, expected_output)

    def test_placeholder_finder_multiple_locations_true(self):
        error_file = "./tests_package/ressources/LemmaSeqPrefixNeq_fix_51.dfy_1_0_error"
        method_file = "./tests_package/ressources/LemmaSeqPrefixNeq_fix_51.dfy"
        result_file = (
            "./tests_package/ressources/LemmaSeqPrefixNeq_fix_51.dfy_locations_output"
        )
        method_name = "LemmaSeqPrefixNeq"
        with open(error_file, "r") as file:
            error_message = file.read()

        # copy method file to "/usr/local/home/eric/dafny_repair/NonlinearArithmetic/"
        new_method_path = "/usr/local/home/eric/dafny_repos/libraries/src/Collections/Sequences/LemmaSeqPrefixNeq_51.dfy"
        shutil.copy(method_file, new_method_path)

        try:
            output = call_placeholder_finder(
                error_message, new_method_path, method_name, multiple_locations=True
            )
        except Exception as e:
            print(e)
        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(output, expected_output)

    def test_placeholder_finder_dependencies(self):
        error_file = "./tests_package/ressources/Sqrt2Exists_fix_27.dfy_1_0_error"
        method_file = "./tests_package/ressources/Sqrt2Exists_fix_27.dfy"
        result_file = "./tests_package/ressources/Sqrt2Exists_fix_27.dfy_output"
        method_name = "Sqrt2Exists"
        with open(error_file, "r") as file:
            error_message = file.read()

        new_method_path = "/usr/local/home/eric/dafny_repos/Dafny-VMC/src/Math/Analysis/Sqrt2Exists_fix_27.dfy"
        shutil.copy(method_file, new_method_path)
        output = call_placeholder_finder(
            error_message,
            new_method_path,
            method_name,
            optional_files="/usr/local/home/eric/dafny_repos/Dafny-VMC/src/**/*.dfy",
            blacklisted_file="Reals.dfy",
        )

        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(output, expected_output)

    def test_placeholder_finder_assertion(self):
        error_file = "./tests_package/ressources/FloorIsCorrect_fix_5.dfy_error"
        method_file = "./tests_package/ressources/FloorIsCorrect_fix_5.dfy"
        result_file = "./tests_package/ressources/FloorIsCorrect_fix_5.dfy_output"
        method_name = "FloorIsCorrect"
        with open(error_file, "r") as file:
            error_message = file.read()

        new_method_path = "/usr/local/home/eric/dafny_repos/Dafny-VMC/src/Math/FloorIsCorrect_fix_5.dfy"
        shutil.copy(method_file, new_method_path)
        try:
            output = call_placeholder_finder(
                error_message,
                new_method_path,
                method_name,
                optional_files="/usr/local/home/eric/dafny_repos/Dafny-VMC/src/**/*.dfy",
                blacklisted_file="Rationals.dfy",
            )
        except Exception as e:
            print(e)

        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(output, expected_output)

    def test_placeholder_finder_LHS(self):
        error_file = "./tests_package/ressources/LimitOfMultiplicationWithZeroSequence_fix_24.dfy_error"
        method_file = "./tests_package/ressources/LimitOfMultiplicationWithZeroSequence_fix_24.dfy"
        result_file = "./tests_package/ressources/LimitOfMultiplicationWithZeroSequence_fix_24.dfy_output"
        method_name = "LimitOfMultiplicationWithZeroSequence"
        with open(error_file, "r") as file:
            error_message = file.read()

        new_method_path = "/usr/local/home/eric/dafny_repos/Dafny-VMC/src/Math/Analysis/LimitOfMultiplicationWithZeroSequence_fix_13_1.dfy"
        shutil.copy(method_file, new_method_path)
        try:
            output = call_placeholder_finder(
                error_message,
                new_method_path,
                method_name,
                optional_files="/usr/local/home/eric/dafny_repos/Dafny-VMC/src/**/*.dfy",
                blacklisted_file="Limits.dfy",
            )
        except Exception as e:
            print(e)

        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(output, expected_output)

    def test_placeholder_finder_assertby(self):
        error_file = "./tests_package/ressources/LiftInEventSpaceToResultEventSpace_fix_87.dfy_error"
        method_file = (
            "./tests_package/ressources/LiftInEventSpaceToResultEventSpace_fix_87.dfy"
        )
        result_file = "./tests_package/ressources/LiftInEventSpaceToResultEventSpace_fix_87.dfy_output"
        method_name = "LiftInEventSpaceToResultEventSpace"
        with open(error_file, "r") as file:
            error_message = file.read()

        new_method_path = "/usr/local/home/eric/dafny_repos/Dafny-VMC/src/ProbabilisticProgramming/LiftInEventSpaceToResultEventSpace_fix_87.dfy"
        shutil.copy(method_file, new_method_path)
        try:
            output = call_placeholder_finder(
                error_message,
                new_method_path,
                method_name,
                optional_files="/usr/local/home/eric/dafny_repos/Dafny-VMC/src/**/*.dfy",
                blacklisted_file="Monad.dfy",
            )
        except Exception as e:
            print(e)

        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(output, expected_output)

    def test_placeholder_finder_forall(self):
        error_file = (
            "./tests_package/ressources/ConstantSequenceConverges_fix_15.dfy_error"
        )
        method_file = "./tests_package/ressources/ConstantSequenceConverges_fix_15.dfy"
        result_file = (
            "./tests_package/ressources/ConstantSequenceConverges_fix_15.dfy_output"
        )
        method_name = "ConstantSequenceConverges"
        with open(error_file, "r") as file:
            error_message = file.read()

        new_method_path = "/usr/local/home/eric/dafny_repos/Dafny-VMC/src/Math/Analysis/ConstantSequenceConverges_fix_15.dfy"
        shutil.copy(method_file, new_method_path)
        try:
            output = call_placeholder_finder(
                error_message,
                new_method_path,
                method_name,
                optional_files="/usr/local/home/eric/dafny_repos/Dafny-VMC/src/**/*.dfy",
                blacklisted_file="Limits.dfy",
            )
        except Exception as e:
            print(e)

        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(output, expected_output)

    def test_placeholder_finder_calc(self):
        error_file = "./tests_package/ressources/SampleTerminates_fix_78.dfy_error"
        method_file = "./tests_package/ressources/SampleTerminates_fix_78.dfy"
        result_file = "./tests_package/ressources/SampleTerminates_fix_78.dfy_output"
        method_name = "SampleTerminates"
        with open(error_file, "r") as file:
            error_message = file.read()

        new_method_path = "/usr/local/home/eric/dafny_repos/Dafny-VMC/src/Distributions/Uniform/SampleTerminates_fix_78.dfy"
        shutil.copy(method_file, new_method_path)
        try:
            output = call_placeholder_finder(
                error_message,
                new_method_path,
                method_name,
                optional_files="/usr/local/home/eric/dafny_repos/Dafny-VMC/src/**/*.dfy",
                blacklisted_file="/usr/local/home/eric/dafny_repos/Dafny-VMC/src/Distributions/Uniform/Model.dfy",
            )
        except Exception as e:
            print(e)

        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(output, expected_output)

    def test_placeholder_finder_nested_match(self):
        error_file = "./tests_package/ressources/LubUndefUbUndef_fix_5.dfy_error"
        method_file = "./tests_package/ressources/LubUndefUbUndef_fix_5.dfy"
        result_file = "./tests_package/ressources/LubUndefUbUndef_fix_5.dfy_output"
        method_name = "LubUndefUbUndef"
        with open(error_file, "r") as file:
            error_message = file.read()

        new_method_path = "/usr/local/home/eric/dafny_repos/cedar-spec/cedar-dafny/validation/LubUndefUbUndef_fix_5.dfy"
        shutil.copy(method_file, new_method_path)
        try:
            output = call_placeholder_finder(
                error_message, new_method_path, method_name, multiple_locations=True
            )
        except Exception as e:
            print(e)

        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(output, expected_output)

    def test_placeholder_finder_submodules(self):
        error_file = "./tests_package/ressources/ParseDigitsAndDot_fix_887.dfy_error"
        method_file = "./tests_package/ressources/ParseDigitsAndDot_fix_887.dfy"
        result_file = "./tests_package/ressources/ParseDigitsAndDot_fix_887.dfy_output"
        method_name = "ParseDigitsAndDot"
        with open(error_file, "r") as file:
            error_message = file.read()

        new_method_path = "/usr/local/home/eric/dafny_repos/cedar-spec/cedar-dafny/def/ext/ParseDigitsAndDot_fix_887.dfy"
        shutil.copy(method_file, new_method_path)
        try:
            output = call_placeholder_finder(
                error_message, new_method_path, method_name, multiple_locations=True
            )
        except Exception as e:
            print(e)

        with open(result_file, "r") as file:
            expected_output = file.read()
        os.remove(new_method_path)

        self.assertEqual(output, expected_output)
