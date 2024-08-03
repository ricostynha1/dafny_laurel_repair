import pandas as pd
import os
import subprocess

# dataset = "cedar"
# dataset = "dafnyVMC"
dataset = "libraries"

configs = [
    # "configs/main/config_repos/config_llm_cedar_dynamic.yaml",
    # "configs/main/config_repos/config_llm_cedar_dynamicPlaceholder.yaml",
    # "configs/main/config_repos/config_llm_cedar_placeholder.yaml",
    # "configs/main/config_repos/config_llm_cedar_randomexample.yaml"
    # "configs/main/config_repos/config_llm_libraries_dynamic.yaml",
    # "configs/main/config_repos/config_llm_libraries_placeholder.yaml",
    # "configs/main/config_repos/config_llm_libraries_randomexample.yaml",
    "configs/main/config_repos/config_llm_libraries_dynamicPlaceholder.yaml",
    # "configs/main/config_repos/config_llm_cedar_randomexample.yaml"
    #    "configs/main/config_repos/config_llm_DafnyVMC_dynamicPlaceholder.yaml",
    #    "configs/main/config_repos/config_llm_DafnyVMC_dynamic.yaml",
    #    "configs/main/config_repos/config_llm_DafnyVMC_placeholder.yaml",
    #    "configs/main/config_repos/config_llm_DafnyVMC_randomExample.yaml"
]

benchmarks = {}
df = pd.read_csv(f"./results/placeholder_dataset/{dataset}.csv")
# df = pd.read_csv(f"./results/non_verified_{dataset}.csv")

# Remove duplicates
df.drop_duplicates(subset=["Original Method", "Assertion"], inplace=True)

# Shuffle the dataset
df = df.sample(frac=1).reset_index(drop=True)
print(f"Dataset size: {len(df)}")

# Split out a fixed testing set (e.g., 20% of the data)
test_size = 0.25
# train_df, test_df = train_test_split(df, test_size=test_size, random_state=42)
test_df = df[: int(len(df) * test_size)]
train_df = df[int(len(df) * test_size) :]

# Save the testing file

# Define the split ratios for the training set
train_ratios = [0.0, 0.25, 0.50, 0.75, 1]

training_sets = []
# Create a directory to store the training files

if not os.path.exists(f"./results/example_{dataset}"):
    os.makedirs(f"./results/example_{dataset}")
testing_file = f"./results/example_{dataset}/testing_{dataset}.csv"
test_df.to_csv(testing_file)

t_file = []
for ratio in train_ratios:
    split_df = train_df[: int(len(train_df) * ratio)]
    training_file = f"./results/example_{dataset}/training_{dataset}_{ratio}.csv"
    split_df.to_csv(training_file)
    t_file.append(training_file)
    print(
        f"Training data with {int(ratio*100)}% of the training set saved to 'train_data_{int(ratio*100)}.csv'"
    )
# for ratio in train_ratios:
#     # Calculate the number of samples for this ratio
#     num_samples = int(len(train_df) * ratio)
#     print(f"Number of samples: {num_samples}")

#     # Select a subset of the training set
#     subset = train_df.sample(n=num_samples, random_state=42)

#     # Write this subset to a CSV file

benchmarks[dataset] = {
    "training": t_file,
    "testing": test_df,
    "training_file": t_file,
    "testing_file": testing_file,
}


for config in configs:
    file_path_without_ext = os.path.splitext(config)[0]
    type_config = file_path_without_ext.split("_")[-1]

    if not os.path.exists(f"./results_llm/example_{dataset}"):
        os.makedirs(f"./results_llm/example_{dataset}")
    for i, _ in enumerate(benchmarks[dataset]["training"]):
        output_file = f"./results_llm/example_{dataset}/output_{type_config}_ratio_{int(train_ratios[i] * 100)}_{dataset}.csv"

        command = [
            "poetry",
            "run",
            "python",
            "src/test_harness.py",
            "llm",
            config,
            "-p",
            benchmarks[dataset]["testing_file"],
            "-o",
            output_file,
        ]
        command += ["-t", benchmarks[dataset]["training_file"][i]]

        # display the number of lines of the training file

        # Load the training file
        df = pd.read_csv(benchmarks[dataset]["training_file"][i])

        # Print the number of lines in the training file
        print(f"Number of lines in training file: {len(df)}")

        # Load the testing file
        df = pd.read_csv(benchmarks[dataset]["testing_file"])

        # Print the number of lines in the testing file
        print(f"Number of lines in testing file: {len(df)}")

        print(" ".join(command))
        subprocess.run(command)
