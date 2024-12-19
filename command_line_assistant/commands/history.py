import logging
from argparse import Namespace

from dasbus.error import DBusError

from command_line_assistant.dbus.constants import HISTORY_IDENTIFIER
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
    text = TextRenderer(stream=StdoutStream())
    foreground = "lightblue" if is_assistant else "lightgreen"
    text.update(ColorDecorator(foreground=foreground))
    text.update(EmojiDecorator("🤖"))
    return text


def _initialize_text_renderer() -> TextRenderer:
    text = TextRenderer(stream=StdoutStream())
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

    def run(self) -> None:
        if self._clear:
            return self._clear_history()

        if self._first:
            return self._retrieve_first_conversation()

        if self._last:
            return self._retrieve_last_conversation()

        return self._retrieve_all_conversations()

    def _retrieve_all_conversations(self):
        """Retrieve and display all conversations from history."""
        try:
            logger.info("Getting all conversations from history.")
            response = self._proxy.GetHistory()
            history = HistoryEntry.from_structure(response)

            if history.entries:
                for entry in history.entries:
                    self._user_renderer.render(f"Query: {entry.query}")
                    self._assistant_renderer.render(f"Answer: {entry.response}")
                    self._text_renderer.render(f"Time: {entry.timestamp}")
                    self._text_renderer.render(
                        "-" * 50
                    )  # Separator between conversations
            else:
                print("No history found.")
        except DBusError as e:
            logger.info("Failed to get history: %s", e)
            raise e

    def _retrieve_first_conversation(self):
        try:
            logger.info("Getting first conversation from history.")
            response = self._proxy.GetFirstConversation()
            history = HistoryEntry.from_structure(response)
            if history.entries:
                # Display the conversation
                entry = history.entries[0]
                self._user_renderer.render(f"Query: {entry.query}")
                self._assistant_renderer.render(f"Answer: {entry.response}")
                self._text_renderer.render(f"Time: {entry.timestamp}")
            else:
                print("No history found.")
        except DBusError as e:
            logger.info("Failed to get first conversation: %s", e)
            raise e

    def _retrieve_last_conversation(self):
        try:
            logger.info("Getting last conversation from history.")
            response = self._proxy.GetLastConversation()

            # Handle and display the response
            history = HistoryEntry.from_structure(response)
            if history.entries:
                # Display the conversation
                entry = history.entries[0]
                self._user_renderer.render(f"Query: {entry.query}")
                self._assistant_renderer.render(f"Answer: {entry.response}")
                self._text_renderer.render(f"Time: {entry.timestamp}")
            else:
                print("No history found.")
        except DBusError as e:
            logger.info("Failed to get last conversation: %s", e)
            raise e

    def _clear_history(self) -> None:
        try:
            logger.info("Cleaning the history.")
            self._proxy.ClearHistory()
        except DBusError as e:
            logger.info("Failed to clean the history: %s", e)
            raise e


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
