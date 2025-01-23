"""Main module for the cli."""

import sys
from argparse import ArgumentParser, Namespace

from command_line_assistant.commands import history, query
from command_line_assistant.utils.cli import (
    add_default_command,
    create_argument_parser,
    read_stdin,
)
from command_line_assistant.utils.renderers import create_error_renderer


def register_subcommands() -> ArgumentParser:
    """Register all the subcommands for the CLI

    Returns:
        ArgumentParser: The parser with all the subcommands registered.
    """
    parser, commands_parser = create_argument_parser()

    # TODO: add autodetection of BaseCLICommand classes in the future so we can
    # just drop new subcommand python modules into the directory and then loop
    # and call `register_subcommand()` on each one.
    query.register_subcommand(commands_parser)  # type: ignore
    history.register_subcommand(commands_parser)  # type: ignore

    return parser


def initialize() -> int:
    """Main function for the cli entrypoint

    Returns:
        int: Status code of the execution
    """
    parser = register_subcommands()
    error_renderer = create_error_renderer()

    try:
        stdin = read_stdin()

        args = add_default_command(stdin, sys.argv)

        # Small workaround to include the stdin in the namespace object in case it exists.
        namespace = Namespace(stdin=stdin) if stdin else Namespace()
        args = parser.parse_args(args, namespace=namespace)

        if not hasattr(args, "func"):
            parser.print_help()
            return 1

        service = args.func(args)
        return service.run()
    except ValueError as e:
        error_renderer.render(str(e))
        return 1
