"""Module to handle the history command."""

from argparse import Namespace

from command_line_assistant.dbus.constants import HISTORY_IDENTIFIER
from command_line_assistant.dbus.exceptions import (
    CorruptedHistoryError,
    MissingHistoryFileError,
)
from command_line_assistant.dbus.structures import HistoryEntry, HistoryItem
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
)
from command_line_assistant.rendering.renders.spinner import SpinnerRenderer
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_spinner_renderer,
    create_text_renderer,
)


class HistoryCommand(BaseCLICommand):
    """Class that represents the history command."""

    def __init__(self, clear: bool, first: bool, last: bool) -> None:
        """Constructor of the class.

        Note:
            If none of the above is specified, the command will retrieve all
            user history.

        Args:
            clear (bool): If the history should be cleared
            first (bool): Retrieve only the first conversation from history
            last (bool): Retrieve only last conversation from history
        """
        self._clear = clear
        self._first = first
        self._last = last

        self._proxy = HISTORY_IDENTIFIER.get_proxy()

        self._spinner_renderer: SpinnerRenderer = create_spinner_renderer(
            message="Loading history",
            decorators=[EmojiDecorator(emoji="U+1F916")],
        )
        self._q_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator("lightgreen")]
        )
        self._a_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator("lightblue")]
        )
        self._text_renderer: TextRenderer = create_text_renderer()
        self._error_renderer: TextRenderer = create_error_renderer()

        super().__init__()

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Status code of the execution.
        """
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
            self._error_renderer.render(str(e))
            return 1

    def _retrieve_all_conversations(self) -> None:
        """Retrieve and display all conversations from history."""
        self._text_renderer.render("Getting all conversations from history.")
        response = self._proxy.GetHistory()
        history = HistoryEntry.from_structure(response)

        # Display the conversation
        self._show_history(history.entries)

    def _retrieve_first_conversation(self) -> None:
        """Retrieve the first conversation in the conversation cache."""
        self._text_renderer.render("Getting first conversation from history.")
        response = self._proxy.GetFirstConversation()
        history = HistoryEntry.from_structure(response)

        # Display the conversation
        self._show_history(history.entries)

    def _retrieve_last_conversation(self):
        """Retrieve the last conversation in the conversation cache."""
        self._text_renderer.render("Getting last conversation from history.")
        response = self._proxy.GetLastConversation()

        # Handle and display the response
        history = HistoryEntry.from_structure(response)

        # Display the conversation
        self._show_history(history.entries)

    def _clear_history(self) -> None:
        """Clear the user history"""
        self._text_renderer.render("Cleaning the history.")
        self._proxy.ClearHistory()

    def _show_history(self, entries: list[HistoryItem]) -> None:
        """Internal method to show the history in a standarized way

        Args:
            entries (list[HistoryItem]): The list of entries in the history
        """
        if not entries:
            self._text_renderer.render("No history found.")
            return

        is_separator_needed = len(entries) > 1
        for entry in entries:
            self._q_renderer.render(f"Query: {entry.query}")
            self._a_renderer.render(f"Answer: {entry.response}")

            timestamp = f"Time: {entry.timestamp}"
            self._text_renderer.render(timestamp)

            if is_separator_needed:
                # Separator between conversations
                self._text_renderer.render("-" * len(timestamp))


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the root parser.

    Args:
        parser (SubParsersAction): Root parser to register command-specific arguments
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
    """Internal command factory to create the command class

    Args:
        args (Namespace): The arguments processed with argparse.

    Returns:
        HistoryCommand: Return an instance of class
    """
    return HistoryCommand(args.clear, args.first, args.last)
