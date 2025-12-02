"""Main module for the cli."""

import logging
import os
import sys
from argparse import ArgumentParser, Namespace

from dasbus.error import DBusError

from command_line_assistant.commands.chat import chat_command
from command_line_assistant.commands.cli import (
    add_default_command,
    create_argument_parser,
    read_stdin,
    register_all_commands,
)
from command_line_assistant.commands.feedback import feedback_command
from command_line_assistant.commands.history import history_command
from command_line_assistant.commands.shell import shell_command
from command_line_assistant.logger import setup_client_logging
from command_line_assistant.rendering.renderers import Renderer
from command_line_assistant.rendering.theme import Theme


def register_subcommands() -> ArgumentParser:
    """Register all the subcommands for the CLI

    Returns:
        ArgumentParser: The parser with all the subcommands registered.
    """
    parser, commands_parser = create_argument_parser()

    # Register all decorator-based commands (includes chat, feedback, history, shell, example)
    register_all_commands(
        commands_parser,
        [chat_command, feedback_command, history_command, shell_command],
    )

    return parser


logger = logging.getLogger(__name__)


def main() -> int:
    """Main function for the cli entrypoint

    Returns:
        int: Status code of the execution
    """
    parser = register_subcommands()

    # Create the error and warning renderers, checking very early if the user
    # specified the --plain flag. This allows the exceptions below that use
    # these renders to follow the user's preference.
    plain_in_argv = "-p" in sys.argv or "--plain" in sys.argv
    renderer = Renderer(plain=plain_in_argv, theme=Theme())

    try:
        stdin = read_stdin()
        modified_args = add_default_command(stdin, sys.argv)

        # In case that the user only calls `chat`, or anything else,
        # we just print help and return with os.EX_USAGE.
        if (
            len(modified_args) <= 1
            and not stdin
            and all(word not in modified_args for word in ("feedback", "history"))
        ):
            parser.print_help()
            return os.EX_USAGE

        # Small workaround to include the stdin in the namespace object. If it
        # exists, it will have the value of the stdin redirection, otherwise,
        # it will be None.
        namespace = Namespace(stdin=stdin)
        parsed_args = parser.parse_args(modified_args, namespace=namespace)
        if not hasattr(parsed_args, "func"):
            parser.print_help()
            return os.EX_USAGE

        # In case the uder specify the --debug, we will enable the logging here.
        if parsed_args.debug:
            setup_client_logging()

        return parsed_args.func(parsed_args)

    except ValueError as e:
        renderer.error(str(e))
        return os.EX_DATAERR
    except DBusError as e:
        renderer.error(str(e))
        return os.EX_UNAVAILABLE
    except RuntimeError as e:
        logger.debug(str(e))
        renderer.error("Oops! Something went wrong while processing your request.")
        renderer.warning(
            "Try submitting your request one more time or contact an administrator."
        )
        return os.EX_SOFTWARE
    except KeyboardInterrupt:
        renderer.error("Keyboard interrupt detected. Exiting...")
        return os.EX_OK


if __name__ == "__main__":
    sys.exit(main())
