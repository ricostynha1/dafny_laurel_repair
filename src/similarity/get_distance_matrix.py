import ast
import os
import pandas as pd
import pickle
import sys

sys.path.append("/exp/dafny_repair/src/")
from token_wrapper import parse_token_output, call_tokenizer_csharp
from dafny_utils import extract_dafny_functions

from similarity import mss


def process_method(original_file, original_method):
    with open(original_file, "r") as f:
        original_file_content = f.read()
    original_method_content = extract_dafny_functions(
        original_file_content, original_method
    )
    tokens = parse_token_output(call_tokenizer_csharp(original_method_content))
    return original_method_content, tokens


def process_assertion(assertion):
    tokens = parse_token_output(call_tokenizer_csharp(assertion))
    return assertion, tokens


def comparator(x, y):
    return mss.MostSimilarSubsequence(x, y, comp=mss.line_comp).similarity("mean")


def compute_clustering(suggestions, pickle_file, method="complete"):
    if os.path.exists(pickle_file):
        with open(pickle_file, "rb") as f:
            return pickle.load(f)
    clustering = mss.HierarchicalClustering(
        suggestions,
        comparator,
        method=method,
    )
    with open(pickle_file, "wb") as f:
        pickle.dump(clustering, f)
    return clustering


def compute_clustering_unsave(suggestions):
    clustering = mss.HierarchicalClustering(
        suggestions,
        comparator,
        method="complete",
    )
    return clustering


def get_tokens_df(tokens_file):
    if os.path.exists(tokens_file):
        df_non_verified = pd.read_csv(tokens_file)
        return df_non_verified

    df_non_verified = pd.DataFrame()
    projects = ["cedar", "libraries", "dafnyVMC"]
    for project in projects:
        FILEPATH_NON_VERIFIED = f"/exp/dafny_repair/results/non_verified_{project}.csv"
        df_project = pd.read_csv(FILEPATH_NON_VERIFIED)
        ## add a column to the df with the name of the project
        df_project["project"] = project
        df_non_verified = df_non_verified.append(df_project)

    assertions_raw, assertions_tokens = [], []
    methods_raw, methods_tokens = [], []
    for index, row in df_non_verified.iterrows():
        new_method_path = os.path.join(
            "/exp/dafny_repair/results/" + os.path.basename(row["New Method File"])
        )
        method_content, method_tokens = process_method(
            new_method_path, row["New Method"]
        )
        assertion_content, assertion_tokens = process_assertion(row["Assertion"])
        assertions_raw.append(assertion_content)
        assertions_tokens.append(assertion_tokens)
        methods_raw.append(method_content)
        methods_tokens.append(method_tokens)

    df_non_verified["New Method Tokens"] = methods_tokens
    df_non_verified["Assertion Tokens"] = assertions_tokens

    df_non_verified.to_csv(tokens_file, index=False)
    return df_non_verified


if __name__ == "__main__":
    tokens_file = "/exp/dafny_repair/results/non_verified_tokens.csv"
    df_non_verified = get_tokens_df(tokens_file)
    assertions_tokens = df_non_verified["Assertion Tokens"].apply(ast.literal_eval)
    methods_tokens = df_non_verified["New Method Tokens"].apply(ast.literal_eval)
    mspc = compute_clustering(
        assertions_tokens, "/exp/dafny_repair/results/non_verified_assertions.pkl"
    )
    mspc = compute_clustering(
        methods_tokens, "/exp/dafny_repair/results/non_verified_methods.pkl"
    )
