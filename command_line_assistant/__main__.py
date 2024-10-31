import logging
import os
import sys
from pathlib import Path

from command_line_assistant.cli import get_args
from command_line_assistant.config import (
    load_config_file,
)
from command_line_assistant.handlers import (
    handle_history_write,
    handle_query,
    handle_script_session,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


def main():
    parser, args = get_args()

    config_file = Path(args.config).expanduser()
    config = load_config_file(config_file)

    enforce_script_session = config.output.enforce_script
    output_file = config.output.file

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
        handle_history_write(config, [], "")
    if args.query_string:
        handle_query(args.query_string, config)


if __name__ == "__main__":
    main()
