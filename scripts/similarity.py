import os
import pandas as pd
import matplotlib.pyplot as plt

lengths = {"libraries": 58, "cedar": 54, "dafnyVMC": 33}
type_exp = [
    "placeholder",
    "randomExamples",
    "dynamic",
    "dynamicPlaceholder",
    "EmbeddedPlaceholder",
    "TFIDFPlaceholder",
]

# for placeholder and baseline can you use the same file and method as placeholder.py

RESULT_PATH = "./saved_results/"
benchmarks = ["libraries", "cedar", "dafnyVMC"]
successes_data = {}
overall_data = {}
for benchmark in benchmarks:
    for method in type_exp:
        df = pd.DataFrame()
        if method in ["placeholder", "baseline"]:
            if benchmark == "dafnyVMC":
                df = pd.read_csv(RESULT_PATH + f"output_{method}_vmc-basic.csv")
                print(f"Reading {RESULT_PATH}output_{method}_vmc-basic.csv")
            else:
                df = pd.read_csv(RESULT_PATH + f"output_{method}_{benchmark}-basic.csv")
                print(f"Reading {RESULT_PATH}output_{method}_{benchmark}-basic.csv")
        else:
            for i in range(58):
                if os.path.exists(
                    f"{RESULT_PATH}tmp_{benchmark}/output_{method}-r3_{benchmark}_{i}.csv"
                ):
                    df_temp = pd.read_csv(
                        f"{RESULT_PATH}tmp_{benchmark}/output_{method}-r3_{benchmark}_{i}.csv"
                    )
                    print(
                        f"Reading {RESULT_PATH}tmp_{benchmark}/output_{method}-r3_{benchmark}_{i}.csv"
                    )

                    df_temp["Index"] = i
                    df = pd.concat([df, df_temp], ignore_index=True)
        overall_data[(method, benchmark)] = df

        cumulative_successes = []
        for try_number in range(11):
            successes = df[
                (df["New Method Result"] == "Correct") & (df["Try"] <= try_number)
            ]
            cumulative_successes.append(successes["Index"].nunique())

            successes_data[(method, benchmark)] = cumulative_successes

normalized_cumulative_success = {}

total_successes = {}
total_task = 0
total_task_per_benchmark = {}
seen = []
for (method, benchmark), cumulative_successes in successes_data.items():
    total_indices = overall_data[(method, benchmark)]["Index"].nunique()
    total_indices = lengths[benchmark]
    normalized_cumulative_success[(method, benchmark)] = [
        100.0 * successes / total_indices for successes in cumulative_successes
    ]
    if benchmark not in seen:
        total_task_per_benchmark[benchmark] = total_indices
        total_task += total_indices
        seen.append(benchmark)
    if method not in total_successes:
        total_successes[method] = cumulative_successes
    else:
        total_successes[method] = [
            x + y for x, y in zip(total_successes[method], cumulative_successes)
        ]


for method in total_successes:
    total_successes[method] = [100.0 * x / total_task for x in total_successes[method]]

fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(15, 12))
colors = ["c", "g", "m", "y", "k", "r"]
color_map = {
    method: colors[i % len(colors)]
    for i, method in enumerate(
        ["dynamic", "placeholder", "randomExamples", "dynamicPlaceholder"]
    )
}
type_exp = ["placeholder", "randomExamples", "dynamic", "dynamicPlaceholder"]
axs = axs.flatten()

i = 1
for benchmark in benchmarks:
    for method in type_exp:
        data = normalized_cumulative_success[(method, benchmark)]
        method_name = method
        if method == "randomExamples":
            method_name = "random"
        if method == "dynamic":
            method_name = "similarity-no-placeholder"
        if method == "dynamicPlaceholder":
            method_name = "similarity"
        axs[i].plot(data, label=method_name, color=color_map[method])
        benchmark_name = benchmark
        if benchmark == "dafnyVMC":
            benchmark_name = "vmc"
        axs[i].set_title(f"{benchmark_name}", fontsize=15)
        axs[i].set_xlabel("Number of attempts", fontsize=15)
        axs[i].legend(loc="lower right", fontsize=10)
        axs[i].set_ylabel("Percentage of verified lemmas", fontsize=15)
        # axs[i].legend()
    i += 1
for method, data in total_successes.items():
    if method in type_exp:
        method_name = method
        if method == "randomExamples":
            method_name = "random"
        if method == "dynamic":
            method_name = "similarity-no-placeholder"
        if method == "dynamicPlaceholder":
            method_name = "similarity"
        axs[0].plot(data, label=method_name, color=color_map[method])
        axs[0].set_title("Entire dataset", fontsize=15)
        axs[0].set_xlabel("Number of attempts", fontsize=15)
        axs[0].set_ylabel("Percentage of verified lemmas", fontsize=15)
        axs[0].legend(loc="lower right", fontsize=10)

for spine in axs[0].spines.values():
    spine.set_edgecolor("black")
    spine.set_linewidth(3)
plt.tight_layout()
plt.savefig("./fig/whole_benchs_similarity_script.pdf", bbox_inches="tight")

dafny_gym_fig, ax = plt.subplots(figsize=(10, 6))

type_exp = [
    "placeholder",
    "randomExamples",
    "dynamicPlaceholder",
]
for method, data in total_successes.items():
    if method in type_exp:
        method_name = method
        if method == "EmbeddedPlaceholder":
            method_name = "embedded"
        if method == "TFIDFPlaceholder":
            method_name = "tfidf"
        if method == "randomExamples":
            method_name = "random"
        if method == "dynamic-r2" or method == "dynamicPlaceholder":
            method_name = "similarity"
        ax.plot(data, label=method, color=color_map[method])
        ax.set_ylim(0, 60)  # Set the y-axis limits
        ax.set_xlabel("Number of attempts", fontsize=15)
        ax.set_ylabel("Percentage of verified lemmas", fontsize=15)
        ax.legend(fontsize=10)

plt.savefig("./fig/benchs_similarity_script_single_plot.pdf", bbox_inches="tight")
for spine in ax.spines.values():
    spine.set_edgecolor("black")
    spine.set_linewidth(3)
plt.tight_layout()
plt.show()

type_exp = [
    "randomExamples",
    "dynamicPlaceholder",
    "EmbeddedPlaceholder",
    "TFIDFPlaceholder",
]

fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(15, 12))
colors = ["c", "g", "m", "y", "k", "r"]
color_map = {
    method: colors[i % len(colors)]
    for i, method in enumerate(
        [
            "dynamic",
            "placeholder",
            "randomExamples",
            "dynamicPlaceholder",
            "EmbeddedPlaceholder",
            "TFIDFPlaceholder",
        ]
    )
}
axs = axs.flatten()

i = 1
for benchmark in benchmarks:
    # axs[i](figsize=(10, 6))
    for method in type_exp:
        data = normalized_cumulative_success[(method, benchmark)]
        method_name = method
        if method == "EmbeddedPlaceholder":
            method_name = "embedded"
        if method == "TFIDFPlaceholder":
            method_name = "tfidf"
        if method == "randomExamples":
            method_name = "random"
        if method == "dynamic-r2" or method == "dynamicPlaceholder":
            method_name = "similarity"
        axs[i].plot(data, label=method_name, color=color_map[method])
        benchmark_name = benchmark
        if benchmark == "dafnyVMC":
            benchmark_name = "vmc"
        axs[i].set_title(f"{benchmark_name}", fontsize=15)
        axs[i].set_xlabel("Number of attempts", fontsize=15)
        axs[i].legend(loc="lower right", fontsize=10)
        axs[i].set_ylabel("Percentage of verified lemmas", fontsize=15)
    i += 1

for method, data in total_successes.items():
    if method in type_exp:
        method_name = method
        if method == "EmbeddedPlaceholder":
            method_name = "embedded"
        if method == "TFIDFPlaceholder":
            method_name = "tfidf"
        if method == "randomExamples":
            method_name = "random"
        if method == "dynamic-r2" or method == "dynamicPlaceholder":
            method_name = "similarity"
        axs[0].plot(data, label=method_name, color=color_map[method])
        axs[0].set_title("Entire dataset", fontsize=15)
        axs[0].set_xlabel("Number of attempts", fontsize=15)
        axs[0].set_ylabel("Percentage of verified lemmas", fontsize=15)
        axs[0].legend(loc="lower right", fontsize=10)

for spine in axs[0].spines.values():
    spine.set_edgecolor("black")
    spine.set_linewidth(3)
plt.tight_layout()
plt.savefig("./fig/whole_benchs_similarity_cmp_script.pdf", bbox_inches="tight")
