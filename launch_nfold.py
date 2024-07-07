import pandas as pd
import os
import subprocess
from sklearn.model_selection import KFold


dataset = "cedar"

configs = [
    #    "configs/main/config_repos/config_llm_cedar_static.yaml",
    "configs/main/config_repos/config_llm_cedar_dynamic.yaml",
    #    "configs/main/config_repos/config_llm_cedar_placeholder.yaml",
    #    "configs/main/config_repos/config_llm_cedar_randomExamples.yaml"
    #    "configs/main/config_repos/config_llm_DafnyVMC_static.yaml",
    #    "configs/main/config_repos/config_llm_DafnyVMC_dynamic.yaml",
    #    "configs/main/config_repos/config_llm_DafnyVMC_placeholder.yaml",
    #    "configs/main/config_repos/config_llm_DafnyVMC_randomExample.yaml"
]

benchmarks = {}
df = pd.read_csv(f"./results/placeholder_dataset/{dataset}.csv")
# df = pd.read_csv(f"./results/non_verified_{dataset}.csv")

# remove duplicates
df.drop_duplicates(subset=["Original Method", "Assertion"], inplace=True)

k = len(df)

# rewrite the path of "New Method File" but keep the same file name
df["New Method File"] = df["New Method File"].apply(
    lambda x: os.path.join("./results/", os.path.basename(x))
)


kf = KFold(n_splits=k)

training_sets = []
testing_sets = []

for train_index, test_index in kf.split(df):
    training = df.iloc[train_index]
    testing = df.iloc[test_index]
    training_sets.append(training)
    testing_sets.append(testing)
if not os.path.exists(f"./results/tmp_{dataset}"):
    os.makedirs(f"./results/tmp_{dataset}")
training_files = []
testing_files = []
for i, (training, testing) in enumerate(zip(training_sets, testing_sets)):
    training_file = f"./results/tmp_{dataset}/training_{dataset}_k{k}_{i}.csv"
    testing_file = f"./results/tmp_{dataset}/testing_{dataset}_k{k}_{i}.csv"
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
            "src/test_harness.py",
            "llm",
            config,
            "-p",
            benchmarks[dataset]["testing_file"][i][:],
            "-o",
            output_file,
        ]
        command += ["-t", benchmarks[dataset]["training_file"][i][:]]
        print(" ".join(command))
        subprocess.run(command)
