import argparse
import logging
import os
import sys

from command_line_assistant.handlers import (
    handle_history_write,
    handle_query,
    handle_script_session,
)
from command_line_assistant.utils import read_stdin, read_yaml_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


def get_args():
    parser = argparse.ArgumentParser(
        description="A script with multiple optional arguments and a required positional argument if no optional arguments are provided."
    )

    parser.add_argument(
        "--history-clear", action="store_true", help="Clear the history."
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Initialize a script session (all other arguments will be ignored).",
    )
    parser.add_argument(
        "--config",
        default=os.getenv("COMMAND_LINE_ASSISTANT_CONFIG", "config.yaml"),
        help="Path to the config file.",
    )

    # Positional argument, required only if no optional arguments are provided
    parser.add_argument("query_string", nargs="?", help="Query string to be processed.")

    args = parser.parse_args()
    optional_args = [
        args.history_clear,
        args.record,
    ]
    input_data = read_stdin()
    if not args.query_string and input_data:
        logging.debug("stdin detected")
        args.query_string = input_data.strip()

    if not any(optional_args) and not args.query_string:
        parser.error("Query string is required if no optional arguments are provided.")
    return parser, args


def main():
    parser, args = get_args()

    config = read_yaml_config(args.config)
    if not config:
        logging.warning(
            "Config file not found. Script will continue with default values."
        )

    output_capture_conf = config.get("output_capture", {})
    enforce_script_session = output_capture_conf.get("enforce_script", False)
    output_file = output_capture_conf.get(
        "output_file", "/tmp/command-line-assistant_output.txt"
    )

    if enforce_script_session and (not args.record or not os.path.exists(output_file)):
        parser.error(
            f"Please call `{sys.argv[0]} --record` first to initialize script session or create the output file.",
            file=sys.stderr,
        )

    # NOTE: This needs more refinement, script session can't be combined with other arguments
    if args.record:
        handle_script_session(output_file)
        exit(0)
    if args.history_clear:
        logging.info("Clearing history of conversation")
        handle_history_write(config.get("history", {}), [], "")
    if args.query_string:
        handle_query(args.query_string, config)


if __name__ == "__main__":
    main()
