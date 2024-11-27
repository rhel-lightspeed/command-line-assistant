import argparse
import sys

from command_line_assistant.commands import add_default_command
from command_line_assistant.commands.history import HistoryCommand
from command_line_assistant.commands.query import QueryCommand


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the argument parser for command line assistant."""
    parser = argparse.ArgumentParser(
        description="A script with multiple optional arguments and a required positional argument if no optional arguments are provided.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="0.1.0",
        default=argparse.SUPPRESS,
        help="Show command line assistant version and exit.",
    )
    commands_parser = parser.add_subparsers(
        dest="command", help="command line assistant helpers"
    )

    QueryCommand.register_subcommand(commands_parser)  # type: ignore
    HistoryCommand.register_subcommand(commands_parser)  # type: ignore

    return parser


def main() -> int:
    parser = create_argument_parser()

    args = add_default_command(sys.argv[1:])
    args = parser.parse_args(args)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    service = args.func(args)
    service.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
