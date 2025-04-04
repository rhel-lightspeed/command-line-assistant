"""Main module for the cli."""

import logging
import os
import sys
from argparse import ArgumentParser, Namespace

from dasbus.error import DBusError

from command_line_assistant.commands import chat, feedback, history, shell
from command_line_assistant.logger import setup_client_logging
from command_line_assistant.utils.cli import (
    add_default_command,
    create_argument_parser,
    read_stdin,
)
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_warning_renderer,
)


def register_subcommands() -> ArgumentParser:
    """Register all the subcommands for the CLI

    Returns:
        ArgumentParser: The parser with all the subcommands registered.
    """
    parser, commands_parser = create_argument_parser()

    chat.register_subcommand(commands_parser)  # type: ignore
    feedback.register_subcommand(commands_parser)  # type: ignore
    history.register_subcommand(commands_parser)  # type: ignore
    shell.register_subcommand(commands_parser)  # type: ignore

    return parser


logger = logging.getLogger(__name__)


def initialize() -> int:
    """Main function for the cli entrypoint

    Returns:
        int: Status code of the execution
    """
    parser = register_subcommands()
    error_renderer = create_error_renderer()
    warning_renderer = create_warning_renderer()

    os.environ["NO_COLOR"] = "1"

    try:
        stdin = read_stdin()
        args = add_default_command(stdin, sys.argv)
        # Small workaround to include the stdin in the namespace object. If it
        # exists, it will have the value of the stdin redirection, otherwise,
        # it will be None.
        namespace = Namespace(stdin=stdin)
        args = parser.parse_args(args, namespace=namespace)
        if not hasattr(args, "func"):
            parser.print_help()
            return 1

        # In case the uder specify the --debug, we will enable the logging here.
        if args.debug:
            setup_client_logging()

        service = args.func(args)
        return service.run()
    except (ValueError, DBusError) as e:
        error_renderer.render(str(e))
        return 1
    except RuntimeError as e:
        logger.debug(str(e))
        error_renderer.render(
            "Oops! Something went wrong while processing your request."
        )
        warning_renderer.render(
            "Try submitting your request one more time or contact an administrator."
        )
        return 1
    except KeyboardInterrupt:
        error_renderer.render("Uh, oh! Keyboard interrupt detected.")
        return 1
