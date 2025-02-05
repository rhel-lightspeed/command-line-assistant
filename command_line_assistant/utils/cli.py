"""
Utilitary module to interact with the CLI. This olds the basic implementation
that is reused across commands and other interactions.
"""

import argparse
import dataclasses
import getpass
import os
import select
import sys
from abc import ABC, abstractmethod
from argparse import SUPPRESS, ArgumentParser, _SubParsersAction
from pathlib import Path
from typing import Optional

from command_line_assistant.constants import VERSION

# Define the type here so pyright is happy with it.
SubParsersAction = _SubParsersAction

GLOBAL_FLAGS: list[str] = ["--debug", "--version", "-v", "-h", "--help"]
ARGS_WITH_VALUES: list[str] = ["--clear"]

OS_RELEASE_PATH = Path("/etc/os-release")


@dataclasses.dataclass
class CommandContext:
    """A context for all commands with useful information.

    Note:
        This is meant to be initialized exclusively by the client.

    Attributes:
        username (str): The username of the current user.
        effective_user_id (int): The effective user id.
        os_release (dict[str, str]): A dictionary with the OS release information.
    """

    username: str = getpass.getuser()
    effective_user_id: int = os.getegid()

    # Empty dictionary for os_release information. Parsed at the __post__init__ method.
    os_release: dict[str, str] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        """Post init method to parse the OS Release file.

        Raises:
            ValueError: If the OS Release file is not found.
        """
        try:
            contents = OS_RELEASE_PATH.read_text()
            # Clean the empty lines
            contents = [content for content in contents.splitlines() if content]
            for line in contents:
                splitted_line = line.strip().split("=", 1)
                key = splitted_line[0].lower()
                value = splitted_line[1].strip('"')
                self.os_release[key] = value
        except FileNotFoundError as e:
            raise ValueError("OS Release file not found.") from e


class BaseCLICommand(ABC):
    """Absctract class to define a CLI Command."""

    def __init__(self) -> None:
        """Constructor for the base class."""
        self._context: CommandContext = CommandContext()
        super().__init__()

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

    global_flags = []
    command_args = []
    for arg in args:
        if arg in GLOBAL_FLAGS:
            global_flags.append(arg)
        else:
            command_args.append(arg)

    subcommand = _subcommand_used(argv)
    if not subcommand:
        return global_flags + ["chat"] + command_args
    return args


def _subcommand_used(args: list[str]) -> Optional[str]:
    """Return what subcommand has been used by the user. Return None if no subcommand has been used.

    Arguments:
        args (list[str]): The arguments from the command line

    Returns:
        Optional[str]: If we find a match for the argument, we return it, otherwise we return None.
    """
    for index, argument in enumerate(args):
        # It means that we hit a --version/--help
        if argument in GLOBAL_FLAGS:
            continue

        # If we have a exact match for any of the commands, return directly
        if argument in ("chat", "history", "shell"):
            return argument

        # Otherwise, check if this is the second part of an arg that takes a value.
        elif index > 0 and args[index - 1] in ARGS_WITH_VALUES:
            continue

    return None


def create_argument_parser() -> tuple[ArgumentParser, SubParsersAction]:
    """Create the argument parser for command line assistant.

    Returns:
        tuple[ArgumentParser, SubParsersAction]: The parent and subparser created
    """
    parser = ArgumentParser(
        prog="c",
        description="The Command Line Assistant powered by RHEL Lightspeed is an optional generative AI assistant available within the RHEL command line interface.",
        add_help=False,
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging information"
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=VERSION,
        default=SUPPRESS,
        help="Show program version",
    )
    commands_parser = parser.add_subparsers(dest="command")
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
        try:
            input_data = sys.stdin.read().strip()
        except UnicodeDecodeError as e:
            raise ValueError("Binary input are not supported.") from e

        return input_data

    # If no input, return None or handle as you prefer
    return None
