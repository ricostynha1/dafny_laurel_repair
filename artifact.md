# OOPSLA artifact

## Intro

This artifact contains the github repository `https://github.com/emugnier/dafny_repair` also available on Zenodo with:
- the Laurel tool
    - the assertion placeholder algorithm
    - the algorithm for in-context example selection
- the DafnyGym benchmark
- scripts to run the paper experiments

We are only going for the Available, Functionnal and maybe reusable badge.
Our experiments take 3 days to be fully reproduced, therefore we advise to reproduce the graphs using our saved results.

**We are aware that they are issues with the Docker container, we are working on resolving them.**

## Hardware dependencies

No particular hardware dependencies are required. The Docker image is less than 2GB, and the experiments can be run on a laptop.
The main requirement is to have an internet connection to be able to call the GPT API. You need to have a GPT API with some credits to run the experiments.

Although unlikely, hardware differences might affect the verification results.

## Getting Started

### Setup the Environment

Add the OpenAI key to the secrets file at `./.secrets.yaml`:
```
OPENAI_API_KEY: HASH_OF_THE_KEY
```

Instruction for the Docker image:
```sh
docker build -t laurel .
docker run -it -v ./.secrets.yaml:/dafny_repair/.secrets.yaml -v ./fig:/dafny_repair/fig -p 8866:8866 -p 8889:8889 laurel
```

All of the following commands should be run in the Docker container.

### Generate one assertion

```bash
make gen_report_getting_started
```
You should now be able to click on the link that appears on your terminal and inspect the results.

## Step by step

### Laurel configuration

To run the different experiments with different settings you can use the different configurations available in `configs/main`.
They follow this format:
```
Results_dir: PATH_WHERE_TO_STORE_THE_RESULTS
Prompts:
  - Context:
      Question_prompt: "Can you fix this proof by inserting one assertion in the <assertion> placeholder?"
      Training_file: DEFAULT_TRAINING_FILE_IF_NONE_IS_PROVIDED_USING_THE_t_OPTION
      Max_size: MAXIMUM_NUMBER_OF_EXAMPLE
    System_prompt: |
      "You are a Dafny formal method expert.
      You will be provided with a Dafny method indicated by the delimiter <method>
      that does not verify.
      Your task is to insert an assertion in the <assertion> placeholder to make it verify. Your answer must start with `assert`."
    Fix_prompt: "Can you fix this proof by inserting one assertion in the <assertion> placeholder?"
    Method_context: "None"
    Feedback: True|False (Include error message in prompt)
    Nb_tries: 10
    Error_feedback: True|False (Provide the error if the assertion generated fails)
    Prompt_name: "dynamicPlaceholder"
    Type: TYPE_OF_EXAMPLE_SELECTION ["Dynamic", "Embedding", "TFIDF", "FileProvided"]
    Placeholder: True

Model_parameters:
  # Same paramater as the OpenAI API
  Temperature: 1
  Model: gpt-4o
  Max_tokens: 2048
  Prompt_limit: 8192
  Encoding: "cl100k_base"

# Specific Dafny verification flags
Dafny_args: "--library /usr/local/home/eric/dafny_repos/Dafny-VMC/src/**/*.dfy --resource-limit 20000"
Results_file: ./results_llm/stats_llm_DafnyVMC_sample10_placeholder_4t.csv
```

### Running Laurel

```sh
python laurel_main.py llm <config_file> [options]
```

#### Arguments

- `config_file`: The configuration file to run the LLM generation.

Options:
- `--pruning_results`, `-p`: pruning results file.
- `--output_file`, `-o`: Output result file.
- `--training_file`, `-t`: Training file.
- `--method_to_process`, `-m`: Index of the Method to process (integer).

#### Example

```sh
python laurel_main.py llm config.yaml -p pruning.csv -o output.csv -t training.csv -m 1
```

### Main experiment script
To facilitate the experiments, we created scripts that run laurel using the different configurations and benchmarks.

To run the Placeholder experiments (RQ1 and RQ2):
```sh
make run_placeholder
```

### Generate the graphs

This command will generate the graphs from the saved results so that you do not have to rerun the whole experiments.
```sh
make generate_graphs
```
You will find the newly generated graphs in the `./fig` directory.

## Reusability

### Structure of the code

```
.
├── configs
│   └── main
│       └── config_repos # Configurations for the experiments
├── fig
├── laurel
│   ├── placeholder_finder # Algorithm for placeholder
│   ├── similarity # Algorithm for example selection
│   │   ├── mss
│   └── tokenizer_csharp # Convert Dafny code to Tokens
├── logs
├── notebooks
├── results
```
