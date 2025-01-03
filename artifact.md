# OOPSLA artifact

## Intro

This artifact contains:
- the Laurel tool
    - the assertion placeholder algorithm
    - the algorithm for in-context example selection
- the DafnyGym benchmark
- scripts to run the paper experiments and generate the figures

## Hardware dependencies

No particular hardware dependencies are required. The Docker image is less than 2GB, and the experiments can be run on a laptop.
The main requirement is to have an internet connection to be able to call the GPT API. You need to have a GPT API with some credits to run the experiments.

Although unlikely, hardware differences might affect the verification results.

## Getting Started

### Setup the Environment

Instruction for the Docker image
Use a key

### Generate one assertion

Example on one assertion generation that work
Without example:
```bash
make run_lib_baseline
```

With example:
```bash
make run_lib_similarity
```

View a report summary:
```bash
make launch_report
```

## Step by step

How to write a config
Laurel command
The main script to run our experiments
Generate the graphs

## Reusability

Structure of the code
Algorithm for placeholder
Algorithm for example selection
DafnyGym
