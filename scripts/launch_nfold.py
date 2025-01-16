import argparse
import pandas as pd
import os
import subprocess
from sklearn.model_selection import KFold


# dataset = "cedar"
# dataset = "dafnyVMC"
# Create the parser
parser = argparse.ArgumentParser(description="Launch Nfold experiement for similarity")

# Add the arguments
parser.add_argument("--dataset", type=str, required=True, help="The dataset to use")

# Parse the arguments
args = parser.parse_args()

# Use the dataset argument
dataset = args.dataset
if dataset not in ["cedar", "DafnyVMC", "libraries"]:
    raise ValueError("dataset must be one of cedar, DafnyVMC, libraries")


configs = [
    "configs/main/config_repos/config_llm_cedar_dynamic.yaml",
    "configs/main/config_repos/config_llm_cedar_dynamicPlaceholder.yaml",
    "configs/main/config_repos/config_llm_cedar_placeholder.yaml",
    "configs/main/config_repos/config_llm_cedar_randomExamples.yaml",
    "configs/main/config_repos/config_llm_libraries_TFIDFPlaceholder.yaml",
    "configs/main/config_repos/config_llm_libraries_EmbeddedPlaceholder.yaml",
    "configs/main/config_repos/config_llm_libraries_dynamic.yaml",
    "configs/main/config_repos/config_llm_libraries_placeholder.yaml",
    "configs/main/config_repos/config_llm_libraries_randomExamples.yaml",
    "configs/main/config_repos/config_llm_libraries_dynamicPlaceholder.yaml",
    "configs/main/config_repos/config_llm_libraries_TFIDFPlaceholder.yaml",
    "configs/main/config_repos/config_llm_libraries_EmbeddedPlaceholder.yaml",
    "configs/main/config_repos/config_llm_DafnyVMC_dynamicPlaceholder.yaml",
    "configs/main/config_repos/config_llm_DafnyVMC_dynamic.yaml",
    "configs/main/config_repos/config_llm_DafnyVMC_placeholder.yaml",
    "configs/main/config_repos/config_llm_DafnyVMC_randomExample.yaml",
    "configs/main/config_repos/config_llm_DafnyVMC_TFIDFPlaceholder.yaml",
    "configs/main/config_repos/config_llm_DafnyVMC_EmbeddedPlaceholder.yaml",
]

# only select configs that contain the dataset name
configs = [config for config in configs if dataset in config]
print(configs)

benchmarks = {}
dataset_name = dataset
if dataset == "DafnyVMC":
    dataset_name = "vmc"
df = pd.read_csv(f"./DafnyGym/{dataset_name}.csv")

# remove duplicates
df.drop_duplicates(subset=["Original Method", "Assertion"], inplace=True)

k = len(df)

# rewrite the path of "New Method File" but keep the same file name
# df["New Method File"] = df["New Method File"].apply(
#     lambda x: os.path.join("./results/", os.path.basename(x))
# )


kf = KFold(n_splits=k)

training_sets = []
testing_sets = []

for train_index, test_index in kf.split(df):
    training = df.iloc[train_index]
    testing = df.iloc[test_index]
    training_sets.append(training)
    testing_sets.append(testing)
# if not os.path.exists(f"./results/tmp_{dataset}"):
#     os.makedirs(f"./results/tmp_{dataset}")
training_files = []
testing_files = []
for i, (training, testing) in enumerate(zip(training_sets, testing_sets)):
    training_file = (
        f"./DafnyGym/tmp_{dataset_name}/training_{dataset_name}_k{k}_{i}.csv"
    )
    testing_file = f"./DafnyGym/tmp_{dataset_name}/testing_{dataset_name}_k{k}_{i}.csv"
    # check that these files exist
    if not os.path.exists(training_file) or not os.path.exists(testing_file):
        raise ValueError(f"Files {training_file} or {testing_file} do not exist")
    training_files.append(training_file)
    testing_files.append(testing_file)
benchmarks[dataset] = {
    "training": training_sets,
    "testing": testing_sets,
    "training_file": training_files,
    "testing_file": testing_files,
}


for config in configs:
    file_path_without_ext = os.path.splitext(config)[0]
    type_config = file_path_without_ext.split("_")[-1]

    if not os.path.exists(f"./results_llm/tmp_{dataset}"):
        os.makedirs(f"./results_llm/tmp_{dataset}")
    for i, _ in enumerate(benchmarks[dataset]["training"]):
        output_file = (
            f"./results_llm/tmp_{dataset}/output_{type_config}-r3_{dataset}_{i}.csv"
        )

        command = [
            "poetry",
            "run",
            "python",
            "laurel/laurel_main.py",
            "llm",
            config,
            "-p",
            benchmarks[dataset]["testing_file"][i][:],
            "-o",
            output_file,
        ]
        command += ["-t", benchmarks[dataset]["training_file"][i][:]]

        subprocess.run(command, check=True)
