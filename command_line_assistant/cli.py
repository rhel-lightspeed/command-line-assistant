import argparse
import logging

from command_line_assistant.config import CONFIG_DEFAULT_PATH
from command_line_assistant.utils import read_stdin


def get_args():
    """Handle CLI options."""
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
        default=CONFIG_DEFAULT_PATH,
        help="Path to the config file.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging in terminal."
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
