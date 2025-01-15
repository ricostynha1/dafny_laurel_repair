import os
import pickle

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
