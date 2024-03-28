import argparse
import yaml
import subprocess
import urllib.parse
import os

SERVER_NAME = "TEST"


def generate_notebook_url(output_files):
    query_params = {
        f"output_file_{i}": output_file for i, output_file in enumerate(output_files)
    }

    encoded_params = urllib.parse.urlencode(query_params)

    full_url = SERVER_NAME + "?" + encoded_params
    return full_url


if __name__ == "__main__":
    # Create the parser and add argument
    parser = argparse.ArgumentParser(description="Launch experiments.")
    parser.add_argument("config_file", type=str, help="Path to the configuration file")

    # Parse the arguments
    args = parser.parse_args()

    # Load the data from exp.yaml
    with open(args.config_file, "r") as file:
        data = yaml.safe_load(file)

    output_files = []
    # Run a command for each combination of config and bench
    for benchmarck in data["Benchmarcks"]:
        bench = benchmarck["Name"]
        for config in benchmarck["Configs"]:
            file_path_without_ext = os.path.splitext(config)[0]
            type_config = file_path_without_ext.split("_")[-1]

            output_file = f"./results_llm/output_{type_config}_{bench}.csv"

            command = [
                "poetry",
                "run",
                "python",
                "src/test_harness.py",
                "llm",
                config,  # Replace with the name of the config
                "-p",
                benchmarck["Content"],  # Replace with the name of the bench
                "-o",
                output_file,  # Replace with the name of the output file
            ]
            print(" ".join(command))
            subprocess.run(command)

            output_files.append(output_file)
    url = generate_notebook_url(output_files)
    print(url)
