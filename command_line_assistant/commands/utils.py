from abc import ABC, abstractmethod
from argparse import SUPPRESS, ArgumentParser, _SubParsersAction

# Define the type here so pyright is happy with it.
SubParsersAction = _SubParsersAction


class BaseCLICommand(ABC):
    @abstractmethod
    def run(self):
        raise NotImplementedError("Not implemented in base class.")


PARENT_ARGS = ["--version", "-v", "-h", "--help"]
ARGS_WITH_VALUES = ["--clear"]


def add_default_command(argv):
    """Add the default command when none is given"""
    args = argv[1:]

    # Early exit if we don't have any argv
    if not args:
        return args

    subcommand = _subcommand_used(argv)
    if subcommand is None:
        args.insert(0, "query")

    return args


def _subcommand_used(args):
    """Return what subcommand has been used by the user. Return None if no subcommand has been used."""
    for index, argument in enumerate(args):
        # If we have a exact match for any of the commands, return directly
        if argument in ("query", "history"):
            return argument

        # It means that we hit a --version/--help
        if argument in PARENT_ARGS:
            return argument

        # Otherwise, check if this is the second part of an arg that takes a value.
        elif args[index - 1] in ARGS_WITH_VALUES:
            continue

    return None


def create_argument_parser() -> tuple[ArgumentParser, SubParsersAction]:
    """Create the argument parser for command line assistant."""
    parser = ArgumentParser(
        description="A script with multiple optional arguments and a required positional argument if no optional arguments are provided.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="0.1.0",
        default=SUPPRESS,
        help="Show command line assistant version and exit.",
    )
    commands_parser = parser.add_subparsers(
        dest="command", help="command line assistant helpers"
    )

    return parser, commands_parser
