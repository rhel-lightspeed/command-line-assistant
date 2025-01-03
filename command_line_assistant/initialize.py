"""Main module for the cli."""

import sys
from argparse import ArgumentParser, Namespace

from command_line_assistant.commands import history, query, record
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import EmojiDecorator
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import (
    add_default_command,
    create_argument_parser,
    read_stdin,
)


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
    record.register_subcommand(commands_parser)  # type: ignore

    return parser


def initialize() -> int:
    """Main function for the cli entrypoint

    Returns:
        int: Status code of the execution
    """
    parser = register_subcommands()

    stdin = None
    try:
        stdin = read_stdin()
    except UnicodeDecodeError:
        # Usually happens when the user try to cat a binary file and redirect that to us.
        text_renderer = TextRenderer()
        text_renderer.update(ColorDecorator(foreground="red"))
        text_renderer.update(EmojiDecorator(emoji="U+1F641"))
        text_renderer.render(
            "The stdin provided could not be decoded. Please, make sure it is in textual format."
        )
        return 1

    args = add_default_command(stdin, sys.argv)

    # Small workaround to include the stdin in the namespace object in case it exists.
    namespace = Namespace(stdin=stdin) if stdin else Namespace()
    args = parser.parse_args(args, namespace=namespace)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    service = args.func(args)
    service.run()
    return 0
