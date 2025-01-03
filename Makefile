run_lib_baseline:
	poetry run python laurel/laurel_main.py llm configs/main/config_repos/config_llm_libraries_baseline.yaml -p DafnyGym/libraries.csv -m 52
run_lib_similarity:
	@if [ ! -d "DafnyGym/tmp_libraries" ]; then \
		poetry run python laurel/nfold.py; \
	fi
	poetry run python laurel/laurel_main.py llm configs/main/config_repos/config_llm_libraries_dynamicPlaceholder.yaml -p DafnyGym/libraries.csv -t DafnyGym/tmp_libraries/training_libraries_k58_52.csv -m 52
test:
	 poetry run python -m unittest discover -s ./tests_package
exp_placeholder:
	 python laurel/exp_launcher.py ./configs/main/exp.yaml
