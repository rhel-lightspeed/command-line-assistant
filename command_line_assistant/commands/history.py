import logging
from argparse import Namespace

from command_line_assistant.dbus.constants import HISTORY_IDENTIFIER
from command_line_assistant.dbus.exceptions import (
    CorruptedHistoryError,
    MissingHistoryFileError,
)
from command_line_assistant.dbus.structures import HistoryEntry
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
    TextWrapDecorator,
)
from command_line_assistant.rendering.renders.spinner import SpinnerRenderer
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.rendering.stream import StdoutStream
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction

logger = logging.getLogger(__name__)


def _initialize_spinner_renderer() -> SpinnerRenderer:
    spinner = SpinnerRenderer(message="Loading history", stream=StdoutStream(end=""))
    spinner.update(TextWrapDecorator())

    return spinner


def _initialize_qa_renderer(is_assistant: bool = False) -> TextRenderer:
    text = TextRenderer(stream=StdoutStream(end="\n"))
    foreground = "lightblue" if is_assistant else "lightgreen"
    text.update(ColorDecorator(foreground=foreground))
    text.update(EmojiDecorator("🤖"))
    return text


def _initialize_text_renderer() -> TextRenderer:
    text = TextRenderer(stream=StdoutStream(end="\n"))
    return text


class HistoryCommand(BaseCLICommand):
    def __init__(self, clear: bool, first: bool, last: bool) -> None:
        self._clear = clear
        self._first = first
        self._last = last

        self._proxy = HISTORY_IDENTIFIER.get_proxy()
        self._user_renderer = _initialize_qa_renderer()
        self._assistant_renderer = _initialize_qa_renderer(is_assistant=True)
        self._text_renderer = _initialize_text_renderer()
        self._spinner_renderer = _initialize_spinner_renderer()

        super().__init__()

    def run(self) -> int:
        try:
            if self._clear:
                self._clear_history()

            if self._first:
                self._retrieve_first_conversation()

            if self._last:
                self._retrieve_last_conversation()

            if not self._last and not self._clear and not self._first:
                self._retrieve_all_conversations()

            return 0
        except (MissingHistoryFileError, CorruptedHistoryError) as e:
            self._text_renderer.update(ColorDecorator(foreground="red"))
            self._text_renderer.update(EmojiDecorator(emoji="U+1F641"))
            self._text_renderer.render(str(e))
            return 1

    def _retrieve_all_conversations(self) -> None:
        """Retrieve and display all conversations from history."""
        self._text_renderer.render("Getting all conversations from history.")
        response = self._proxy.GetHistory()
        history = HistoryEntry.from_structure(response)

        if not history.entries:
            self._text_renderer.render("No history found.")
            return

        for entry in history.entries:
            self._user_renderer.render(f"Query: {entry.query}")
            self._assistant_renderer.render(f"Answer: {entry.response}")
            self._text_renderer.render(f"Time: {entry.timestamp}")
            self._text_renderer.render("-" * 50)  # Separator between conversations

    def _retrieve_first_conversation(self) -> None:
        logger.info("Getting first conversation from history.")
        response = self._proxy.GetFirstConversation()
        history = HistoryEntry.from_structure(response)

        if not history.entries:
            self._text_renderer.render("No history found.")
            return

        entry = history.entries[0]
        self._user_renderer.render(f"Query: {entry.query}")
        self._assistant_renderer.render(f"Answer: {entry.response}")
        self._text_renderer.render(f"Time: {entry.timestamp}")

    def _retrieve_last_conversation(self):
        logger.info("Getting last conversation from history.")
        response = self._proxy.GetLastConversation()

        # Handle and display the response
        history = HistoryEntry.from_structure(response)

        if not history.entries:
            self._text_renderer.render("No history found.")
            return

        # Display the conversation
        entry = history.entries[-1]
        self._user_renderer.render(f"Query: {entry.query}")
        self._assistant_renderer.render(f"Answer: {entry.response}")
        self._text_renderer.render(f"Time: {entry.timestamp}")

    def _clear_history(self) -> None:
        self._text_renderer.render("Cleaning the history.")
        self._proxy.ClearHistory()


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the datasets-cli

    Args:
        parser: Root parser to register command-specific arguments
    """
    history_parser = parser.add_parser(
        "history",
        help="Manage conversation history",
    )
    history_parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the history.",
    )
    history_parser.add_argument(
        "--first",
        action="store_true",
        help="Get the first conversation from history.",
    )
    history_parser.add_argument(
        "--last",
        action="store_true",
        help="Get the last conversation from history.",
    )
    history_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> HistoryCommand:
    return HistoryCommand(args.clear, args.first, args.last)
