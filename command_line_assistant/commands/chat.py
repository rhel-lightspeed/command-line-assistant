"""Module to handle the chat command."""

import argparse
from argparse import Namespace
from io import TextIOWrapper
from typing import Optional

from command_line_assistant.dbus.constants import CHAT_IDENTIFIER
from command_line_assistant.dbus.exceptions import (
    CorruptedHistoryError,
    MissingHistoryFileError,
    RequestFailedError,
)
from command_line_assistant.dbus.structures import Message, MessageInput
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
    WriteOnceDecorator,
)
from command_line_assistant.rendering.renders.spinner import SpinnerRenderer
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction
from command_line_assistant.utils.files import (
    guess_mimetype,
)
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


def _parse_attachment_file(attachment: Optional[TextIOWrapper] = None) -> str:
    """Parse the attachment file and read its contents.

    Args:
        attachment (Optional[TextIOWrapper], optional): The attachment that will be parsed

    Returns:
        str: Either the str read or None.
    """
    if not attachment:
        return ""

    try:
        return attachment.read().strip()
    except UnicodeDecodeError as e:
        raise ValueError(
            "File appears to be binary or contains invalid text encoding"
        ) from e


class ChatCommand(BaseCLICommand):
    """Class that represents the chat command."""

    def __init__(
        self,
        query_string: Optional[str] = "",
        stdin: Optional[str] = "",
        attachment: Optional[TextIOWrapper] = None,
    ) -> None:
        """Constructor of the class.

        Args:
            query_string (Optional[str], optional): The query provided by the user.
            stdin (Optional[str], optional): The user redirect input from stdin
            attachment (Optional[TextIOWrapper], optional): The file attachment from the user
        """
        self._query = query_string.strip() if query_string else ""
        self._stdin = stdin.strip() if stdin else ""

        # Initialize it as None before we read and manipulate the rest.
        self._attachment = _parse_attachment_file(attachment)
        self._attachment_mimetype = guess_mimetype(attachment)

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

        self._proxy = CHAT_IDENTIFIER.get_proxy()

        super().__init__()

    def _get_input_source(self) -> str:
        """Determine and return the appropriate input source based on combination rules.

        Warning:
            This is set to be deprecated in the future when we normalize the API backend to accept the context and works with it.

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
        # Rule 7: All three present - positional and file take precedence
        if all([self._query, self._stdin, self._attachment]):
            self._warning_renderer.render(
                "Using positional query and file input. Stdin will be ignored."
            )
            return f"{self._query} {self._attachment}"

        # Rule 6: Positional + file
        if self._query and self._attachment:
            return f"{self._query} {self._attachment}"

        # Rule 5: Stdin + file
        if self._stdin and self._attachment:
            return f"{self._stdin} {self._attachment}"

        # Rule 4: Stdin + positional
        if self._stdin and self._query:
            return f"{self._query} {self._stdin}"

        # Rules 1-3: Single source - return first non-empty source
        source = next(
            (src for src in [self._query, self._stdin, self._attachment] if src),
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
                message_input = MessageInput()
                message_input.from_dict(
                    data={
                        "question": question,
                        "stdin": self._stdin,
                        "attachment_contents": self._attachment,
                        "attachment_mimetype": self._attachment_mimetype,
                        "user": self._context.effective_user_id,
                    }
                )
                response = self._proxy.AskQuestion(
                    MessageInput.to_structure(message_input)
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
    chat_parser = parser.add_parser(
        "chat",
        help="Command to ask a question to the LLM.",
    )
    # Positional argument, required only if no optional arguments are provided
    chat_parser.add_argument(
        "query_string", nargs="?", help="The question that will be sent to the LLM"
    )
    chat_parser.add_argument(
        "-a",
        "--attachment",
        nargs="?",
        type=argparse.FileType("r"),
        help="File attachment to be read and sent alongside the query",
    )

    chat_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> ChatCommand:
    """Internal command factory to create the command class

    Args:
        args (Namespace): The arguments processed with argparse.

    Returns:
        QueryCommand: Return an instance of class
    """
    options = {
        "query_string": args.query_string,
        "stdin": None,
        "attachment": args.attachment,
    }

    # We may not always have the stdin argument in the namespace.
    if "stdin" in args:
        options["stdin"] = args.stdin

    return ChatCommand(**options)
