import argparse

from logger_config import configure_logger
from generating_llm_fix import generate_fix_llm
from pruning import remove_assertions


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run Dafny verification for specified methods."
    )
    parser.add_argument(
        "--disable_date", action="store_true", help="remove date from logs"
    )

    subparsers = parser.add_subparsers(
        dest="mode", help="Choose between llm or remove assertion"
    )

    llm_parser = subparsers.add_parser("llm", help="Use llm mode")
    llm_parser.add_argument("config_file", help="Config to run the llm gen")
    llm_parser.add_argument("--pruning_results", "-p", help="CSV pruning results file")
    llm_parser.add_argument("--output_file", "-o", help="Output_result_file")
    llm_parser.add_argument("--training_file", "-t", help="Training file")
    llm_parser.add_argument(
        "--method_to_process", "-m", help="Method to process", type=int
    )

    prune_assert_parser = subparsers.add_parser(
        "prune-assert", help="Prune-assert mode"
    )
    prune_assert_parser.add_argument("config_file", help="Config to run the llm gen")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    if args.disable_date:
        logger = configure_logger(include_date=False)
    else:
        logger = configure_logger()

    if args.mode == "prune-assert":
        logger.info("==== Starting the assertion pruning ====")
        remove_assertions(args.config_file)
    elif args.mode == "llm":
        logger.info("==== Starting the llm fix ====")
        generate_fix_llm(
            args.config_file,
            pruning_file=args.pruning_results,
            output_file=args.output_file,
            training_file=args.training_file,
            method_to_process=args.method_to_process,
        )
