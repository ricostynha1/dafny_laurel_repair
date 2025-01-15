poetry_install:
	poetry install

run_lib_baseline: poetry_install
	poetry run python laurel/laurel_main.py llm configs/main/config_repos/config_llm_libraries_baseline.yaml -p DafnyGym/libraries.csv -m 52 -o results_llm/lib_baseline.csv
run_lib_similarity: poetry_install
	@if [ ! -d "DafnyGym/tmp_libraries" ]; then \
		cd DafnyGym && poetry run python nfold.py --dataset libraries; \
	fi
	poetry run python laurel/laurel_main.py llm configs/main/config_repos/config_llm_libraries_dynamicPlaceholder.yaml -p DafnyGym/libraries.csv -t DafnyGym/tmp_libraries/training_libraries_k58_52.csv -m 52 -o results_llm/lib_similarity.csv

run_cedar_baseline: poetry_install
	poetry run python laurel/laurel_main.py llm configs/main/config_repos/config_llm_cedar_baseline.yaml -p DafnyGym/cedar.csv -m 10 -o results_llm/cedar_baseline.csv
run_cedar_similarity: poetry_install
	@if [ ! -d "DafnyGym/tmp_cedar" ]; then \
		cd DafnyGym && poetry run python nfold.py --dataset cedar; \
	fi
	poetry run python laurel/laurel_main.py llm configs/main/config_repos/config_llm_cedar_dynamicPlaceholder.yaml -p DafnyGym/cedar.csv -t DafnyGym/tmp_cedar/training_cedar_k54_10.csv -m 10 -o results_llm/cedar_similarity.csv

run_vmc_baseline: poetry_install
	poetry run python laurel/laurel_main.py llm configs/main/config_repos/config_llm_DafnyVMC_baseline.yaml -p DafnyGym/vmc.csv -m 3 -o results_llm/vmc_baseline.csv
run_vmc_similarity: poetry_install
	@if [ ! -d "DafnyGym/tmp_vmc" ]; then \
		cd DafnyGym && poetry run python nfold.py --dataset vmc; \
	fi
	poetry run python laurel/laurel_main.py llm configs/main/config_repos/config_llm_DafnyVMC_dynamicPlaceholder.yaml -p DafnyGym/vmc.csv -t DafnyGym/tmp_vmc/training_vmc_k33_3.csv -m 33 -o results_llm/vmc_similarity.csv

gen_report_getting_started: run_lib_baseline run_lib_similarity run_cedar_baseline run_cedar_similarity run_vmc_baseline run_vmc_similarity
	poetry run voila --Voila.ip='0.0.0.0' --autoreload=True --port 8866 ./notebooks/dashboard.ipynb & poetry run voila --Voila.ip='0.0.0.0' --autoreload=True --port 8889 ./notebooks/getting_started_report.ipynb

exp_placeholder:
	 python laurel/exp_launcher.py ./configs/main/exp.yaml
