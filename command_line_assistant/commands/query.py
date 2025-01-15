"""Module to handle the query command."""

import argparse
from argparse import Namespace
from io import TextIOWrapper
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
from command_line_assistant.utils.files import is_content_in_binary_format
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_spinner_renderer,
    create_text_renderer,
    create_warning_renderer,
)

#: Legal notice that we need to output once per user
LEGAL_NOTICE = (
    "This feature uses AI technology. Do not include personal information or "
    "other sensitive information in your input. Interactions may be used to "
    "improve Red Hat's products or services."
)
#: Always good to have legal message.
ALWAYS_LEGAL_MESSAGE = "Always review AI generated content prior to use."


class QueryCommand(BaseCLICommand):
    """Class that represents the query command."""

    def __init__(
        self,
        query_string: Optional[str] = None,
        stdin: Optional[str] = None,
        input: Optional[TextIOWrapper] = None,
    ) -> None:
        """Constructor of the class.

        Args:
            query_string (Optional[str], optional): The query provided by the user.
            stdin (Optional[str], optional): The user redirect input from stdin
            input (Optional[TextIOWrapper], optional): The file input from the user
        """
        self._query = query_string.strip() if query_string else None
        self._stdin = stdin.strip() if stdin else None
        self._input = input

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
        self._notice_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator(foreground="lightyellow")]
        )
        self._error_renderer: TextRenderer = create_error_renderer()
        self._warning_renderer: TextRenderer = create_warning_renderer()

        self._proxy = QUERY_IDENTIFIER.get_proxy()

        super().__init__()

    def _get_input_source(self) -> str:
        """Determine and return the appropriate input source based on combination rules.

        Rules:
        1. Positional query only -> use positional query
        2. Stdin query only -> use stdin query
        3. File query only -> use file query
        4. Stdin + positional query -> combine as "{positional_query} {stdin}"
        5. Stdin + file query -> combine as "{stdin} {file_query}"
        6. Positional + file query -> combine as "{positional_query} {file_query}"
        7. All three sources -> use only positional and file as "{positional_query} {file_query}"

        Raises:
            ValueError: If no input source is provided

        Returns:
            str: The query string from the selected input source(s)
        """
        file_content = None
        if self._input:
            file_content = self._input.read().strip()
            if is_content_in_binary_format(file_content):
                raise ValueError("File appears to be binary")

            file_content = file_content.strip()

        # Rule 7: All three present - positional and file take precedence
        if all([self._query, self._stdin, file_content]):
            self._warning_renderer.render(
                "Using positional query and file input. Stdin will be ignored."
            )
            return f"{self._query} {file_content}"

        # Rule 6: Positional + file
        if self._query and file_content:
            return f"{self._query} {file_content}"

        # Rule 5: Stdin + file
        if self._stdin and file_content:
            return f"{self._stdin} {file_content}"

        # Rule 4: Stdin + positional
        if self._stdin and self._query:
            return f"{self._query} {self._stdin}"

        # Rules 1-3: Single source - return first non-empty source
        source = next(
            (src for src in [self._query, self._stdin, file_content] if src),
            None,
        )
        if source:
            return source

        raise ValueError(
            "No input provided. Please provide input via file, stdin, or direct query."
        )

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Status code of the execution
        """

        try:
            question = self._get_input_source()
        except ValueError as e:
            self._error_renderer.render(str(e))
            return 1

        output = "Nothing to see here..."

        try:
            with self._spinner_renderer:
                response = self._proxy.AskQuestion(
                    self._context.effective_user_id, question
                )
                output = Message.from_structure(response).message
        except (
            RequestFailedError,
            MissingHistoryFileError,
            CorruptedHistoryError,
        ) as e:
            self._error_renderer.render(str(e))
            return 1

        self._legal_renderer.render(LEGAL_NOTICE)
        self._text_renderer.render(output)
        self._notice_renderer.render(ALWAYS_LEGAL_MESSAGE)
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
    query_parser.add_argument(
        "-i",
        "--input",
        nargs="?",
        type=argparse.FileType("r"),
        help="Read file from user system.",
    )

    query_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> QueryCommand:
    """Internal command factory to create the command class

    Args:
        args (Namespace): The arguments processed with argparse.

    Returns:
        QueryCommand: Return an instance of class
    """
    options = {"query_string": args.query_string, "stdin": None, "input": args.input}

    # We may not always have the stdin argument in the namespace.
    if "stdin" in args:
        options["stdin"] = args.stdin

    return QueryCommand(**options)
