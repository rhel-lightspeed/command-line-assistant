import sys
from pathlib import Path

from command_line_assistant.commands import history, query, record
from command_line_assistant.config import (
    CONFIG_DEFAULT_PATH,
    load_config_file,
)
from command_line_assistant.logger import setup_logging
from command_line_assistant.utils.cli import add_default_command, create_argument_parser


def main() -> int:
    config_file = Path(CONFIG_DEFAULT_PATH)
    config = load_config_file(config_file)

    setup_logging(config, False)

    parser, commands_parser = create_argument_parser()

    # TODO: add autodetection of BaseCLICommand classes in the future so we can just drop
    # new subcommand python modules into the directory and then loop and call `register_subcommand()`
    # on each one.
    query.register_subcommand(commands_parser, config)  # type: ignore
    history.register_subcommand(commands_parser, config)  # type: ignore
    record.register_subcommand(commands_parser, config)  # type: ignore

    args = add_default_command(sys.argv)
    args = parser.parse_args(args)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    service = args.func(args)
    service.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
