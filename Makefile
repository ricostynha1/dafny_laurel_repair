
run_lib:
	poetry run python src/test_harness.py llm configs/config_llm_libraries_sample10.yaml  -p samples/non_verified_libraries_rest.csv
run_lib_static:
	poetry run python src/test_harness.py llm configs/config_llm_libraries_sample10_staticp.yaml  -p samples/non_verified_libraries_rest.csv
run_cedar:
	poetry run python src/test_harness.py llm configs/config_llm_cedar_sample10.yaml  -p samples/non_verified_cedar_sample_10.csv
run_vmc:
	poetry run python src/test_harness.py llm configs/config_llm_DafnyVMC_sample10.yaml  -p results/non_verified_dafnyVMC_sample_10.csv
test:
	 poetry run python -m unittest discover -s ./tests_package
