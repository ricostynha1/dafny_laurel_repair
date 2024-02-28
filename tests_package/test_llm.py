import csv
from generating_llm_fix import generate_fix_llm
import unittest
from unittest.mock import patch
import sys
from io import StringIO

sys.path.append("./src")


class TestsLLM(unittest.TestCase):
    # Test the whole chain
    @patch("generating_llm_fix.upload_results")
    @patch("generating_llm_fix.Llm_prompt.generate_fix")
    def test_generate_fix_llm(self, mock_Llm_prompt, mock_upload_results):
        config_file = "./tests_package/ressources/config_llm_test.yaml"
        pruning_file = "./tests_package/ressources/llm_test.csv"

        mock_upload_results.return_value = True
        mock_Llm_prompt.return_value = """
            lemma UnitIsUnique<T(!new)>(bop: (T, T) -> T, unit1: T, unit2: T)
            requires IsUnital(bop, unit1)
                requires IsUnital(bop, unit2)
                ensures unit1 == unit2
            {
                assert unit1 == bop(unit1, unit2);
                assert unit2 == bop(unit2, unit1);
            }
        """
        original_file = "./tests_package/ressources/unital_pruning.dfy"
        with open(original_file, "r") as file:
            original_content = file.read()

        generate_fix_llm(config_file, pruning_file)

        # check that the result file is correct
        expected_content = """Index,Original Method File,Original Method,Original Method Time,Original Method Result,Original Result File,Original Error Message,Original Error Message File,New Method File,New Method,New Method Time,New Method Result,New Method Result File,New Method Error Message,New Method Error Message File,Prompt File,Prompt Length,Prompt Index,Prompt_name,Diff,Url
0,./tests/ressources/pruned/unital_assert.dfy,UnitIsUnique,0.522336,Errors,./results/UnitIsUnique_0.txt,a postcondition could not be proved on this return path,./results/UnitIsUnique__0_error.txt,./results/UnitIsUnique_fix_0.dfy,UnitIsUnique,0.510024,Correct,./results/UnitIsUnique_fix_0.txt,,,./tests/ressources/unital_assert.dfy_0_prompt,934,1,error_n_feedback,"assert unit1 == bop(unit1, unit2);
assert unit2 == bop(unit2, unit1);
}",http://c10-09.sysnet.ucsd.edu:8866/?results=.%2Ftests_package%2Fressources%2Ffixes_llm_test.csv&assertions=.%2Ftests_package%2Fressources%2Fllm_test.csv&method=0
        """
        with open("tests_package/ressources/fixes_llm_test.csv", "r") as file:
            file_content = file.read()
            self.maxDiff = None

        expected_reader = csv.DictReader(StringIO(expected_content))
        actual_reader = csv.DictReader(StringIO(file_content))

        for expected_row, actual_row in zip(expected_reader, actual_reader):
            for field in expected_row:
                if field not in ["Original Method Time", "New Method Time"]:
                    self.assertEqual(expected_row[field], actual_row[field])
        with open(original_file, "r") as file:
            new_content = file.read()
            self.assertEqual(original_content, new_content)

    @patch("generating_llm_fix.upload_results")
    @patch("generating_llm_fix.Llm_prompt.generate_fix")
    def test_generate_fix_2_tries(self, mock_Llm_prompt, mock_upload_results):
        pruning_file = "./tests_package/ressources/llm_test.csv"
        config_file = "./tests_package/ressources/config_llm_test.yaml"

        mock_upload_results.return_value = True
        incorrect_answer = """
            lemma UnitIsUnique<T(!new)>(bop: (T, T) -> T, unit1: T, unit2: T)
            requires IsUnital(bop, unit1)
                requires IsUnital(bop, unit2)
                ensures unit1 == unit2
            {
                assert unit1 == bop(unit1, unit1);
            }
        """
        correct_answer = """
            lemma UnitIsUnique<T(!new)>(bop: (T, T) -> T, unit1: T, unit2: T)
            requires IsUnital(bop, unit1)
                requires IsUnital(bop, unit2)
                ensures unit1 == unit2
            {
                assert unit1 == bop(unit1, unit2);
                assert unit2 == bop(unit2, unit1);
            }
        """
        mock_Llm_prompt.side_effect = [incorrect_answer, correct_answer]
        # original file
        original_file = "./tests_package/ressources/unital_pruning.dfy"
        with open(original_file, "r") as file:
            original_content = file.read()

        generate_fix_llm(config_file, pruning_file)
        with open(original_file, "r") as file:
            new_content = file.read()
            self.assertEqual(original_content, new_content)
