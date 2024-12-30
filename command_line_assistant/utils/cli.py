"""
Utilitary module to interact with the CLI. This olds the basic implementation
that is reused across commands and other interactions.
"""

import select
import sys
from abc import ABC, abstractmethod
from argparse import SUPPRESS, ArgumentParser, _SubParsersAction
from typing import Optional

from command_line_assistant.constants import VERSION

# Define the type here so pyright is happy with it.
SubParsersAction = _SubParsersAction

PARENT_ARGS: list[str] = ["--version", "-v", "-h", "--help"]
ARGS_WITH_VALUES: list[str] = ["--clear"]


class BaseCLICommand(ABC):
    """Absctract class to define a CLI Command."""

    @abstractmethod
    def run(self) -> int:
        """Entrypoint method for all CLI commands."""


def add_default_command(stdin: Optional[str], argv: list[str]):
    """Add the default command when none is given

    Args:
        stdin (str): The input string coming from stdin
        argv (list[str]): List of arguments from CLI
    """
    args = argv[1:]

    # Early exit if we don't have any argv or stdin
    if not args and not stdin:
        return args

    subcommand = _subcommand_used(argv)
    if subcommand is None:
        args.insert(0, "query")

    return args


def _subcommand_used(args: list[str]):
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
        version=VERSION,
        default=SUPPRESS,
        help="Show command line assistant version and exit.",
    )
    commands_parser = parser.add_subparsers(
        dest="command", help="command line assistant helpers"
    )

    return parser, commands_parser


def read_stdin() -> Optional[str]:
    """Parse the std input when a user give us.

    For example, consider the following scenario:
        >>> echo "how to run podman?" | c

    Or a more complex one
        >>> cat error-log | c "How to fix this?"

    Returns:
        In case we have a stdin, we parse and retrieve it. Otherwise, just
        return None.
    """
    # Check if there's input available on stdin
    if select.select([sys.stdin], [], [], 0.0)[0]:
        # If there is input, read it
        input_data = sys.stdin.read().strip()
        return input_data

    # If no input, return None or handle as you prefer
    return None
