
run_lib:
	poetry run python src/test_harness.py llm configs/config_llm_libraries_sample10.yaml  -p results/testing_libraries_assertion.csv
run_lib_none:
	poetry run python src/test_harness.py llm configs/config_llm_libraries_sample10_none.yaml  -p results/testing_libraries_assertion.csv
run_lib_static:
	poetry run python src/test_harness.py llm configs/config_llm_libraries_sample10_staticp.yaml  -p results/placeholder_dataset/libraries.csv -m 52
run_lib_dynamic:
	poetry run python src/test_harness.py llm configs/config_llm_libraries_sample10_dynamicp.yaml  -p results/testing_libraries_assertion.csv
run_cedar:
	poetry run python src/test_harness.py llm configs/config_llm_cedar_sample10.yaml  -p samples/non_verified_cedar_sample_10.csv
run_cedar_static:
	poetry run python src/test_harness.py llm configs/config_llm_cedar_sample10_static.yaml  -p results/placeholder_dataset/cedar.csv
run_vmc:
	poetry run python src/test_harness.py llm configs/config_llm_DafnyVMC_sample10.yaml  -p results/non_verified_dafnyVMC_sample_10.csv
run_vmc_static:
	poetry run python src/test_harness.py llm configs/main/config_repos/config_llm_DafnyVMC_static.yaml  -p results/placeholder_dataset/dafnyVMC.csv -m 27
run_lib_baseline:
	poetry run python src/test_harness.py llm configs/main/config_repos/config_llm_libraries_baseline.yaml -p results/placeholder_dataset/libraries.csv -m 52
test:
	 poetry run python -m unittest discover -s ./tests_package
exp_placeholder:
	 python src/exp_launcher.py ./configs/main/exp.yaml
