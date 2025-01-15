import os
import pandas as pd
import matplotlib.pyplot as plt

RESULT_PATH = "./saved_results/"

# Harcoded benchmark lengths
# as laurel can skip some during exceptions
lengths = {
    "libraries-basic": 58,
    "cedar-basic": 54,
    "vmc-basic": 33,
    "cedar-basicremain": 57,
}
benchmarks = ["libraries-basic", "cedar-basic", "vmc-basic"]


def get_type_output_file(filename):
    type_analysis = filename.split("_")[1]
    return type_analysis


def get_benchmarck_name(filename):
    type_analysis = filename.split("_")[2].split(".")[0]
    return type_analysis


def get_ouput_files(dir):
    """
    Return all the filenames in the directory that start by output_
    and contain basic
    """
    files = os.listdir(dir)
    output_files = [f for f in files if f.startswith("output_")]
    k_files = [f for f in output_files if "basic" in f]
    return k_files


results = {}
for filename in get_ouput_files(RESULT_PATH):
    type_analysis = get_type_output_file(filename)
    benchmark_name = get_benchmarck_name(filename)
    if os.stat(RESULT_PATH + filename).st_size != 0 and benchmark_name in benchmarks:
        df = pd.read_csv(RESULT_PATH + filename)
        results[(type_analysis, benchmark_name)] = df

normalized_cumulative_success = {}

successes_data = {}

for (method, benchmark), df in results.items():
    cumulative_successes = [0 * 10]
    for try_number in range(1, 11):
        successes = df[
            (df["New Method Result"] == "Correct") & (df["Try"] <= try_number)
        ]
        # Count the number of unique indices that were successful
        cumulative_successes.append(successes["Index"].nunique())

    successes_data[(method, benchmark)] = cumulative_successes

total_successes = {}
total_task = 0
total_task_per_benchmark = {}
seen = []
for (method, benchmark), cumulative_successes in successes_data.items():
    total_indices = results[(method, benchmark)]["Index"].nunique()
    total_indices = lengths[benchmark]
    normalized_cumulative_success[(method, benchmark)] = [
        100.0 * successes / total_indices if total_indices != 0 else 0
        for successes in cumulative_successes
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

grouped_data = {}
for (method, benchmark), data in normalized_cumulative_success.items():
    if benchmark not in grouped_data:
        grouped_data[benchmark] = {}
    grouped_data[benchmark][method] = data


total_normalized_cumulative_success = {}
for benchmark in grouped_data:
    for method in grouped_data[benchmark]:
        if method not in total_normalized_cumulative_success:
            total_normalized_cumulative_success[method] = [0] * 11
        total_normalized_cumulative_success[method] = [
            x + y
            for x, y in zip(
                total_normalized_cumulative_success[method],
                grouped_data[benchmark][method],
            )
        ]

for method, data in total_normalized_cumulative_success.items():
    total_normalized_cumulative_success[method] = [x / len(grouped_data) for x in data]

fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(15, 10))
colors = ["b", "g", "r", "c", "m", "y", "k"]
color_map = {
    method: colors[i % len(colors)]
    for i, method in enumerate(
        [
            "error+placeholder",
            "placeholder",
            "error",
            "baseline",
            "baselineEnhancedPrompt",
            "iterative",
        ]
    )
}
i = 1
axs = axs.flatten()
methods_name = [
    "baseline",
    "error",
    "placeholder",
    "errorplaceholder",
    "errorIterate",
    "baselineEnhancedPrompt",
]
for method, data in total_normalized_cumulative_success.items():
    if method not in methods_name:
        continue
    if method == "errorplaceholder":
        method = "error+placeholder"
    if method == "errorIterate":
        method = "iterative"
    axs[0].plot(data, label=method, color=color_map[method])
    axs[0].set_title("Entire dataset", fontsize=15)
    axs[0].set_xlabel("Number of attempts", fontsize=15)
    axs[0].set_ylabel("Percentage of verified lemmas", fontsize=15)
    axs[0].legend(fontsize=10)

benchmarks = ["libraries-basic", "cedar-basic", "vmc-basic"]
for benchmark in benchmarks:
    for method in methods_name:
        method_name = method
        if method == "errorplaceholder":
            method_name = "error+placeholder"
        if method == "errorIterate":
            method_name = "iterative"
        axs[i].plot(
            grouped_data[benchmark][method],
            label=method_name,
            color=color_map[method_name],
        )
    axs[i].set_title(f"{benchmark[:-6]}", fontsize=15)
    axs[i].set_xlabel("Number of attempts", fontsize=15)
    axs[i].set_ylabel("Percentage of verified lemmas", fontsize=15)
    axs[i].legend(fontsize=10, loc="upper left")
    i += 1
for spine in axs[0].spines.values():
    spine.set_edgecolor("black")
    spine.set_linewidth(3)
plt.tight_layout()
plt.savefig("./fig/benchs_placeholder_script.pdf", bbox_inches="tight")

dafny_gym_fig, ax = plt.subplots(figsize=(10, 6))

for method, data in total_normalized_cumulative_success.items():
    if method not in methods_name:
        continue
    if method == "errorplaceholder":
        method = "error+placeholder"
    if method == "errorIterate":
        method = "iterative"
    ax.plot(data, label=method, color=color_map[method])
    ax.set_ylim(0, 60)  # Set the y-axis limits
    ax.set_xlabel("Number of attempts", fontsize=15)
    ax.set_ylabel("Percentage of verified lemmas", fontsize=15)
    ax.legend(fontsize=10)

plt.savefig("./fig/benchs_placeholder_script_single_plot.pdf", bbox_inches="tight")
for spine in ax.spines.values():
    spine.set_edgecolor("black")
    spine.set_linewidth(3)
plt.tight_layout()
plt.show()
