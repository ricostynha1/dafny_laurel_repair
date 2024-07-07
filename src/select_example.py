import ast
import os
import pandas as pd
import pickle


from token_wrapper import call_tokenizer_csharp, parse_token_output
from dafny_utils import extract_dafny_functions


from similarity.mss import mss
from similarity.get_distance_matrix import compute_clustering_unsave


class ExamplesSelector:
    def __init__(self, config_prompt):
        if config_prompt["Type"] == "Static":
            self.examples = self.init_static_examples(config_prompt)
            self.nature = "Static"
        if config_prompt["Type"] == "Dynamic":
            self.init_dynamic_examples(config_prompt)
            self.nature = "Dynamic"
        if config_prompt["Type"] == "Provided":
            self.examples = self.init_provided_examples(config_prompt)
            self.mspc = None
            self.nature = "Provided"
        if config_prompt["Type"] == "FileProvided":
            self.examples = self.init_file_provided_examples(config_prompt)
            self.nature = "FileProvided"

    def init_file_provided_examples(self, config_prompt):
        training_file = config_prompt["Context"]["Training_file"]
        question_prompt = config_prompt["Context"]["Question_prompt"]

        self.tokens_df = pd.read_csv(training_file)
        selected_rows = self.tokens_df.sample(config_prompt["Context"]["Max_size"])
        self.tokens_df = selected_rows
        examples = []
        for index, row in selected_rows.iterrows():
            question, assertion = self.build_example(index, question_prompt)
            examples.append({"Question": question, "Answer": assertion})
        return examples

    def init_provided_examples(self, config_prompt):
        examples = []
        if config_prompt["Context"] is not None:
            for example in config_prompt["Context"]:
                with open(example["File_to_fix"], "r") as f:
                    # remove the last line since it is the code url
                    # TODO clean that
                    code_to_fix = "\n".join(f.read().split("\n")[:-1])
                user_content = (
                    f"{example['Question_prompt']}\n<method>\n{code_to_fix}\n</method>"
                )

                with open(example["Fix"], "r") as f:
                    # remove the last line since it is the code url
                    # TODO clean that
                    fix = "\n".join(f.read().split("\n")[:-1])
                assistant_content = f"{example['Answer_prompt']} {fix}"
                examples.append({"Question": user_content, "Answer": assistant_content})
        return examples

    # create examples by clustering assertions
    def init_static_examples(self, config_prompt):
        training_file = config_prompt["Context"]["Training_file"]
        threshold = config_prompt["Context"]["Threshold"]
        min_cluster_length = config_prompt["Context"]["Min_cluster_length"]
        token_file = training_file + ".tokens.pkl"
        question_prompt = config_prompt["Context"]["Question_prompt"]

        self.tokens_df, recompute = get_tokens_df(training_file)
        assertion_tokens = self.tokens_df["Assertion Tokens"].to_list()
        if isinstance(self.tokens_df["Assertion Tokens"][0], str):
            assertion_tokens = (
                self.tokens_df["Assertion Tokens"].apply(ast.literal_eval).to_list()
            )
        self.mspc = compute_clustering(assertion_tokens, token_file, force=recompute)
        centers = get_clusters_centers(self.mspc, threshold, min_cluster_length)
        examples = []
        for center in centers:
            question, assertion = self.build_example(center, question_prompt)
            examples.append({"Question": question, "Answer": assertion})
        return examples

    def build_example(self, center, question_prompt, current_file=""):
        if os.path.exists(self.tokens_df["Original File"][center]):
            with open(self.tokens_df["Original File"][center]) as f:
                original_file_content = f.read()
        elif current_file != "":
            with open(current_file) as f:
                original_file_content = f.read()
        else:
            new_method_path = os.path.join(
                os.getcwd()
                + "/results/"
                + os.path.basename(self.tokens_df["New Method File"][center])
            )
            # the assertion that we are looking for is Missing!
            with open(new_method_path) as f:
                original_file_content = f.read()
        original_method_content = extract_dafny_functions(
            original_file_content, self.tokens_df["Original Method"][center]
        )
        assertion = self.tokens_df["Assertion"][center]
        question = build_question(question_prompt, original_method_content, assertion)
        return question, assertion

    def init_dynamic_examples(self, config_prompt):
        training_file = config_prompt["Context"]["Training_file"]
        token_file = training_file + ".method_tokens.pkl"
        self.max_size = config_prompt["Context"]["Max_size"]
        self.tokens_df, recompute = get_tokens_df(training_file)
        # self.tokens_df["Assertion Tokens"]).to_list()
        method_tokens = self.tokens_df["Method Tokens"].to_list()
        if isinstance(self.tokens_df["Method Tokens"][0], str):
            method_tokens = (
                self.tokens_df["Method Tokens"].apply(ast.literal_eval).to_list()
            )
        recompute = False
        self.mspc = compute_clustering(method_tokens, token_file, force=recompute)

    def get_clusters_of_method(self, method, threshold):
        method_tokens = parse_token_output(call_tokenizer_csharp(method))
        obj_index = self.mspc.add_row(method_tokens)
        self.mspc._compute_hac()
        _, clusters_elements = self.mspc.get_cluster_of_obj(obj_index, threshold)
        # remove the method itself
        clusters_elements.remove(obj_index)
        self.mspc.remove_row(obj_index)
        return clusters_elements

    def generate_dynamic_examples(
        self, method, threshold, question_prompt, current_file
    ):
        clusters_elements = self.get_clusters_of_method(method, threshold)
        if len(clusters_elements) > self.max_size:
            subset = []
            new_cluster_elements = []
            for elements in clusters_elements:
                subset.append(self.mspc.objs[elements])
            clusters_subset = compute_clustering_unsave(subset)
            rep_clust = clusters_subset.top_k_clusters(self.max_size)
            new_cluster_elements = []
            for cluster in rep_clust:
                cl = clusters_subset.centroid(cluster)
                new_cluster_elements.append(cl)
            clusters_elements = new_cluster_elements

        examples = []
        for elements in clusters_elements:
            question, assertion = self.build_example(
                elements, question_prompt, current_file=current_file
            )
            examples.append({"Question": question, "Answer": assertion})
            if len(examples) >= self.max_size:
                break
        return examples


def get_clusters_centers(mscp, threshold, min_cluster_length):
    clusters = mscp.clusters_by_k(threshold)

    clusters.sort(key=len, reverse=True)
    clusters = clusters[:min_cluster_length]

    centers = []
    for _, cl in enumerate(clusters[::-1]):
        center = mscp.centroid(cl)
        centers.append(center)
    return centers


def process_assertion(assertion):
    tokens = parse_token_output(call_tokenizer_csharp(assertion))
    return assertion, tokens


def process_method(original_file, original_method):
    with open(original_file, "r") as f:
        original_file_content = f.read()
    original_method_content = extract_dafny_functions(
        original_file_content, original_method
    )
    tokens = parse_token_output(call_tokenizer_csharp(original_method_content))
    return original_method_content, tokens


def get_tokens_df(training_file):
    df_non_verified = pd.read_csv(training_file)
    recompute = False
    if "Assertion Tokens" not in df_non_verified.columns:
        assertions_tokens = []
        for _, row in df_non_verified.iterrows():
            _, assertion_tokens = process_assertion(row["Assertion"])
            assertions_tokens.append(assertion_tokens)
        df_non_verified["Assertion Tokens"] = assertions_tokens
        recompute = True
    if "Method Tokens" not in df_non_verified.columns:
        methods_tokens = []
        for _, row in df_non_verified.iterrows():
            new_method_path = os.path.join(
                os.getcwd() + "/results/" + os.path.basename(row["New Method File"])
            )
            _, method_tokens = process_method(new_method_path, row["New Method"])
            methods_tokens.append(method_tokens)
        df_non_verified["Method Tokens"] = methods_tokens
        recompute = True
    df_non_verified.to_csv(training_file, index=False)
    return df_non_verified, recompute


def comparator(x, y):
    return mss.MostSimilarSubsequence(x, y, comp=mss.line_comp).similarity("mean")


def compute_clustering(suggestions, pickle_file, force=False):
    if os.path.exists(pickle_file) and not force:
        with open(pickle_file, "rb") as f:
            try:
                return pickle.load(f)
            except Exception as e:
                print(
                    f"Error loading pickle file, try recomputing the cluster by setting force=True: {e}"
                )
                raise
    clustering = mss.HierarchicalClustering(
        suggestions,
        comparator,
        method="complete",
    )
    with open(pickle_file, "wb") as f:
        pickle.dump(clustering, f)
    return clustering


def build_question(question, method_to_fix, assertion):
    placeholder = "\n<assertion> Insert the assertion here </assertion>\n"
    method_with_placeholder = replace_assertion_by_placeholder(
        method_to_fix, assertion, placeholder
    )
    return question + "\n" + method_with_placeholder


def replace_assertion_by_placeholder(method_content, assertion, placeholder):
    example = method_content
    example = example.replace(assertion, placeholder)
    return example
