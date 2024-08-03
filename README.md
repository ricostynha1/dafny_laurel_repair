# dafny_repair

Experimental tool for repairing Dafny programs using LLMs.

## DAFNYGYM Benchmarks

By default, the dataset assumes that this repository is located in `/exp/dafny_repair/` and that the different codebases are in `/exp/test_projects`.
THIS CAN BE CHANGED (see installation).

The dataset is based on the following commits for each codebase:

- `cedar-spec` - `2b9a0cbd` [commit](https://github.com/cedar-policy/cedar-spec/commit/2b9a0cbd9af0d3779a613228b40b0146ac9f73ff)
- `Dafny-VMC` - `b79a4c7` [commit](https://github.com/dafny-lang/Dafny-VMC/commit/b79a4c74c253d95448c971d6727b845b67838a4b)
- `libraries` - `ae8708c` [commit](https://github.com/dafny-lang/libraries/commit/ae8708c091d32383235d5d8c15c08cff05613bbc)

## Installation

### Dotnet

```sh
sudo add-apt-repository ppa:dotnet/backports
sudo apt-get update && sudo apt-get install -y dotnet-sdk-6.0
```

### Dafny

For compatibility reasons:

```sh
wget https://github.com/dafny-lang/dafny/releases/download/v4.3.0/dafny-4.3.0-x64-ubuntu-20.04.zip
sudo apt-get install unzip
unzip dafny-4.3.0-x64-ubuntu-20.04.zip
```

Add Dafny to your path. Dafny setup is done.

### Pyenv

```sh
curl https://pyenv.run | bash
```

### Make

```sh
sudo apt-get install make
```

### Poetry

```sh
sudo apt-get install pipx
pipx install poetry
pipx ensurepath
poetry install
```

### Dafny Codebases

Feel free to put them wherever you want.

#### Cedar

```sh
git clone https://github.com/cedar-policy/cedar-spec
cd cedar-spec
git checkout 2b9a0cbd
```

#### Dafny-VMC

```sh
git clone https://github.com/dafny-lang/Dafny-VMC
cd Dafny-VMC
git checkout b79a4c7
```

#### Libraries

```sh
git clone https://github.com/dafny-lang/Dafny-VMC
cd libraries
git checkout ae8708c
```

#### Logs

Create a log directory to run the file at the root of your project:

```sh
mkdir log
```

### Get the results and results_llm directories at the root of the project

```sh
unzip benchmarks.zip
```

### Benchmark Files Changes

Change the `bench/exp/test_projects` directory:

```sh
find . -type f -exec sed -i 's/\/exp\/dafny_repair/\.\//g' {} +
```

Change `/user/local/home/eric/dafny_repos/` to the place where you downloaded the dafny_repos:

```sh
find . -type f -exec sed -i 's/\/exp\/test_projects\//\/usr\/local\/home\/eric\/dafny_repos\//g' {} +
```

### Initialize the Tokenizer

```sh
cd src/tokenizer_csharp && dotnet build
```

### To Commit

```sh
pipx install pre-commit
pre-commit install
```

Then create a `secrets.yaml` file in the project directory with the following content:

```yaml
OPENAI_API_KEY:
GOOGLE_OAUTH_JSON:
```

### Run Make

Execute the following command:

```sh
make run_lib_static
```

### Dataset location

All the assertions are available in `./results/placeholder_dataset/`.

## Run the experiments

For the placeholder experiment:
```
make exp_placeholder
```

For the similarity experiment:
```
poetry run python launch_nfold.py
poetry run python launch_nfold_vmc.py
poetry run python launch_nfold_cedar.py

```
