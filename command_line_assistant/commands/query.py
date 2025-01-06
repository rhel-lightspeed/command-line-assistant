"""Module to handle the query command."""

import getpass
from argparse import Namespace
from typing import Optional

from command_line_assistant.dbus.constants import QUERY_IDENTIFIER
from command_line_assistant.dbus.exceptions import (
    CorruptedHistoryError,
    MissingHistoryFileError,
    RequestFailedError,
)
from command_line_assistant.dbus.structures import Message
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
    WriteOnceDecorator,
)
from command_line_assistant.rendering.renders.spinner import SpinnerRenderer
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_spinner_renderer,
    create_text_renderer,
)

LEGAL_NOTICE = (
    "RHEL Lightspeed Command Line Assistant can answer questions related to RHEL."
    " Do not include personal or business sensitive information in your input."
    "Interactions with RHEL Lightspeed may be reviewed and used to improve our "
    "products and service."
)
#: Legal notice that we need to output once per user
ALWAYS_LEGAL_MESSAGE = (
    "Always check AI/LLM-generated responses for accuracy prior to use."
)
#: Always good to have legal message.


class QueryCommand(BaseCLICommand):
    """Class that represents the query command."""

    def __init__(self, query_string: str, stdin: Optional[str]) -> None:
        """Constructor of the class.

        Args:
            query_string (str): The query provided by the user.
            stdin (Optional[str]): The user redirect input from stdin
        """
        self._query = query_string
        self._stdin = stdin

        self._spinner_renderer: SpinnerRenderer = create_spinner_renderer(
            message="Requesting knowledge from AI",
            decorators=[EmojiDecorator(emoji="U+1F916")],
        )
        self._text_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator(foreground="green")]
        )
        self._legal_renderer: TextRenderer = create_text_renderer(
            decorators=[
                ColorDecorator(foreground="lightyellow"),
                WriteOnceDecorator(state_filename="legal"),
            ]
        )
        self._warning_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator(foreground="lightyellow")]
        )
        self._error_renderer: TextRenderer = create_error_renderer()

        super().__init__()

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Status code of the execution
        """
        proxy = QUERY_IDENTIFIER.get_proxy()

        query = self._query
        if self._stdin:
            # If query is provided, the message becomes "{query} {stdin}",
            # otherwise, to avoid submitting `None` as part of the query, let's
            # default to submit only the stidn.
            query = f"{query} {self._stdin}" if query else self._stdin

        input_query = Message()
        input_query.message = query
        # Get the current user
        input_query.user = getpass.getuser()
        output = "Nothing to see here..."

        try:
            with self._spinner_renderer:
                proxy.ProcessQuery(input_query.to_structure(input_query))
                output = Message.from_structure(proxy.RetrieveAnswer()).message
        except (
            RequestFailedError,
            MissingHistoryFileError,
            CorruptedHistoryError,
        ) as e:
            self._error_renderer.render(str(e))
            return 1

        self._legal_renderer.render(LEGAL_NOTICE)
        self._text_renderer.render(output)
        self._warning_renderer.render(ALWAYS_LEGAL_MESSAGE)
        return 0


def register_subcommand(parser: SubParsersAction) -> None:
    """
    Register this command to argparse so it's available for the root parserself._.

    Args:
        parser (SubParsersAction): Root parser to register command-specific arguments
    """
    query_parser = parser.add_parser(
        "query",
        help="Ask a question and get an answer from LLM.",
    )
    # Positional argument, required only if no optional arguments are provided
    query_parser.add_argument(
        "query_string", nargs="?", help="Query string to be processed."
    )

    query_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> QueryCommand:
    """Internal command factory to create the command class

    Args:
        args (Namespace): The arguments processed with argparse.

    Returns:
        QueryCommand: Return an instance of class
    """
    # We may not always have the stdin argument in the namespace.
    if "stdin" in args:
        return QueryCommand(args.query_string, args.stdin)

    return QueryCommand(args.query_string, None)
