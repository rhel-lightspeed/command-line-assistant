from argparse import Namespace

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
    TextWrapDecorator,
    WriteOnceDecorator,
)
from command_line_assistant.rendering.renders.spinner import SpinnerRenderer
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.rendering.stream import StderrStream, StdoutStream
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction

LEGAL_NOTICE = (
    "RHEL Lightspeed Command Line Assistant can answer questions related to RHEL."
    " Do not include personal or business sensitive information in your input."
    "Interactions with RHEL Lightspeed may be reviewed and used to improve our "
    "products and service."
)
ALWAYS_LEGAL_MESSAGE = (
    "Always check AI/LLM-generated responses for accuracy prior to use."
)


def _initialize_spinner_renderer() -> SpinnerRenderer:
    spinner = SpinnerRenderer(
        message="Requesting knowledge from AI", stream=StdoutStream(end="")
    )

    spinner.update(EmojiDecorator(emoji="U+1F916"))  # Robot emoji
    spinner.update(TextWrapDecorator())

    return spinner


def _initialize_text_renderer() -> TextRenderer:
    text = TextRenderer(stream=StdoutStream(end="\n"))
    text.update(ColorDecorator(foreground="green"))  # Robot emoji
    text.update(TextWrapDecorator())

    return text


def _initialize_legal_renderer(write_once: bool = False) -> TextRenderer:
    text = TextRenderer(stream=StderrStream())
    text.update(ColorDecorator(foreground="lightyellow"))
    text.update(TextWrapDecorator())

    if write_once:
        text.update(WriteOnceDecorator(state_filename="legal"))

    return text


class QueryCommand(BaseCLICommand):
    def __init__(self, query_string: str) -> None:
        self._query = query_string

        self._spinner_renderer: SpinnerRenderer = _initialize_spinner_renderer()
        self._text_renderer: TextRenderer = _initialize_text_renderer()
        self._legal_renderer: TextRenderer = _initialize_legal_renderer(write_once=True)
        self._warning_renderer: TextRenderer = _initialize_legal_renderer()

        super().__init__()

    def run(self) -> int:
        proxy = QUERY_IDENTIFIER.get_proxy()
        input_query = Message()
        input_query.message = self._query

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
            self._text_renderer.update(ColorDecorator(foreground="red"))
            self._text_renderer.update(EmojiDecorator(emoji="U+1F641"))
            self._text_renderer.render(str(e))
            return 1

        self._legal_renderer.render(LEGAL_NOTICE)
        self._text_renderer.render(output)
        self._warning_renderer.render(ALWAYS_LEGAL_MESSAGE)
        return 0


def register_subcommand(parser: SubParsersAction) -> None:
    """
    Register this command to argparse so it's available for the datasets-cli

    Args:
        parser: Root parser to register command-specific arguments
    """
    query_parser = parser.add_parser(
        "query",
        help="ask a question and get an answer from llm.",
    )
    # Positional argument, required only if no optional arguments are provided
    query_parser.add_argument(
        "query_string", nargs="?", help="Query string to be processed."
    )

    query_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> QueryCommand:
    return QueryCommand(args.query_string)
