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
    error_renderer = create_error_renderer(plain=plain_in_argv)
    warning_renderer = create_warning_renderer(plain=plain_in_argv)

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
            return os.EX_USAGE

        error_renderer = create_error_renderer(
            plain=hasattr(args, "plain") and args.plain
        )
        warning_renderer = create_warning_renderer(
            plain=hasattr(args, "plain") and args.plain
        )

        # In case the uder specify the --debug, we will enable the logging here.
        if args.debug:
            setup_client_logging()

        service = args.func(args)
        return service.run()
    except ValueError as e:
        error_renderer.render(str(e))
        return os.EX_DATAERR
    except DBusError as e:
        error_renderer.render(str(e))
        return os.EX_UNAVAILABLE
    except RuntimeError as e:
        logger.debug(str(e))
        error_renderer.render(
            "Oops! Something went wrong while processing your request."
        )
        warning_renderer.render(
            "Try submitting your request one more time or contact an administrator."
        )
        return os.EX_SOFTWARE
    except KeyboardInterrupt:
        error_renderer.render("Keyboard interrupt detected. Exiting...")
        return os.EX_OK


if __name__ == "__main__":
    sys.exit(main())
