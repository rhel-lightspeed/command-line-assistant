"""
Utilitary module to interact with the CLI. This olds the basic implementation
that is reused across commands and other interactions.
"""

import argparse
import dataclasses
import getpass
import logging
import os
import select
import sys
from argparse import SUPPRESS, ArgumentParser, Namespace, _SubParsersAction
from pathlib import Path
from typing import Any, Callable, Optional

from command_line_assistant.constants import VERSION

logger = logging.getLogger(__name__)

# Define the type here so pyright is happy with it.
SubParsersAction = _SubParsersAction

GLOBAL_FLAGS: list[str] = [
    "-p",
    "--plain",
    "--debug",
    "--version",
    "-v",
    "-h",
    "--help",
]
ARGS_WITH_VALUES: list[str] = ["--clear"]

OS_RELEASE_PATH = Path("/etc/os-release")

# Type definitions
CommandFunc = Callable[[Namespace, "CommandContext"], int]
ArgumentSpec = tuple[tuple[str, ...], dict[str, Any]]

# Global storage for registered commands
_commands: dict[str, "Command"] = {}

logger = logging.getLogger(__name__)


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

    # Empty dictionary for os_release information. Parsed at the __post__init__
    # method.
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


def add_default_command(stdin: Optional[str], argv: list[str]):
    """Add the default command when none is given

    Arguments:
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
        if argument in ("chat", "history", "shell", "feedback"):
            return argument

        # Otherwise, check if this is the second part of an arg that takes a value.
        elif index > 0 and args[index - 1] in ARGS_WITH_VALUES:
            continue

    return None


def create_argument_parser() -> tuple[ArgumentParser, SubParsersAction]:
    """Create the argument parser for command line assistant.

    Returns:
        tuple[ArgumentParser, SubParsersAction]: The parent and subparser
        created
    """
    parser = ArgumentParser(
        prog="c",
        description=(
            "The Command Line Assistant powered by RHEL Lightspeed is an "
            "optional generative AI assistant available within the RHEL "
            "command line interface."
        ),
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
        help="Show help message and exit.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=VERSION,
        default=SUPPRESS,
        help="Show program version",
    )
    parser.add_argument(
        "-p",
        "--plain",
        action="store_true",
        help=argparse.SUPPRESS,
        default=True,
    )
    commands_parser = parser.add_subparsers(dest="command")
    return parser, commands_parser


def read_stdin() -> str:
    """Parse the std input when a user give us.

    For example, consider the following scenario:
        >>> echo "how to run podman?" | c

    Or a more complex one
        >>> cat error-log | c "How to fix this?"

    Returns:
        str: Return the stdin that was read or if there is nothing, return an
        empty string.
    """
    # Check if there's input available on stdin
    if select.select([sys.stdin], [], [], 0.0)[0]:
        # If there is input, read it
        try:
            input_data = sys.stdin.read().strip()
        except UnicodeDecodeError as e:
            raise ValueError("Binary input are not supported.") from e

        return input_data

    return ""


def create_subparser(parser: SubParsersAction, name: str, help: str) -> ArgumentParser:
    """Create a subparser with some default options

    Arguments:
        parser (SubParsersAction): The parent subparser to be used
        name (str): The name of the new custom subparser
        help (str): The help message to be displayed with the subparser

    Returns:
        ArgumentParser: A new instance of a ArgumentParser to be used as a command.
    """
    custom_parser = parser.add_parser(
        name,
        help=help,
        add_help=False,
        # Disable abbreviated argument matching. This prevents partial strings
        # from matching to valid options (for example, --from matching to
        # --from-chat).
        allow_abbrev=False,
    )
    custom_parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show help message and exit.",
    )

    return custom_parser


def command(
    name: str, help: Optional[str] = None, description: Optional[str] = None
) -> Callable[[CommandFunc], "Command"]:
    """Decorator to register a command function.

    Args:
        name (str): Command name
        help (Optional[str], optional): Short help text
        description (Optional[str], optional): Longer description

    Returns:
        Callable[[CommandFunc], CommandFunc]: Decorator function
    """

    def decorator(func: CommandFunc) -> Command:
        """Decorator to register a command function.

        Args:
            func (CommandFunc): Command function

        Returns:
            CommandFunc: Command function
        """
        cmd = Command(name, func, help, description)
        _commands[name] = cmd

        logger.debug("Registered command: %s", name)
        return cmd

    return decorator


def argument(*args: str, **kwargs: Any) -> Callable[[CommandFunc], CommandFunc]:
    """Decorator to add arguments to a command.

    Args:
        *args: Positional argument names
        **kwargs: Argument options

    Returns:
        Decorator function
    """

    def decorator(func: CommandFunc) -> CommandFunc:
        """Decorator to add arguments to a command.

        Args:
            func (CommandFunc): Command function

        Returns:
            CommandFunc: Command function
        """
        if not hasattr(func, "_cmd_arguments"):
            func._cmd_arguments = []  # type: ignore

        func._cmd_arguments.append((args, kwargs))  # type: ignore
        return func

    return decorator


class Command:
    """Represents a single CLI command."""

    def __init__(
        self,
        name: str,
        func: CommandFunc,
        help: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Initialize a new command.

        Args:
            name (str): Command name
            func (CommandFunc): Command function
            help (Optional[str], optional): Short help message. Defaults to None.
            description (Optional[str], optional): Longer description. Defaults to None.
        """
        self.name = name
        self.func = func
        self.help = help
        self.description = description
        self.arguments: list[ArgumentSpec] = getattr(func, "_cmd_arguments", [])

    def register(self, parser: _SubParsersAction) -> None:
        """Register this command with the argument parser.

        Args:
            parser (_SubParsersAction): Subparser to register with
        """
        subparser = parser.add_parser(
            self.name, help=self.help, description=self.description
        )

        # Add arguments in reverse order (decorators are applied bottom-up)
        for args, kwargs in reversed(self.arguments):
            subparser.add_argument(*args, **kwargs)

        # Set the command function as default
        subparser.set_defaults(func=self._create_wrapper())

    def _create_wrapper(self) -> Callable[[Namespace], Any]:
        """Create a wrapper function for the command.

        Returns:
            Wrapper function
        """

        def wrapper(args: Namespace) -> Any:
            """Wrapper function for the command.

            Args:
                args (Namespace): Command arguments

            Returns:
                Any: Command result
            """
            context = CommandContext()
            try:
                return self.func(args, context)
            except Exception:
                raise

        return wrapper


def register_all_commands(parser: _SubParsersAction, commands: list[Command]) -> None:
    """Register all commands with the parser.

    Args:
        parser (_SubParsersAction): Subparser to register commands with
    """
    for cmd in commands:
        cmd.register(parser)
