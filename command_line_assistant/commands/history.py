"""Module to handle the history command."""

from argparse import Namespace
from typing import Optional

from command_line_assistant.dbus.constants import (
    CHAT_IDENTIFIER,
    HISTORY_IDENTIFIER,
    USER_IDENTIFIER,
)
from command_line_assistant.dbus.exceptions import (
    ChatNotFoundError,
    CorruptedHistoryError,
    HistoryNotAvailable,
    MissingHistoryFileError,
)
from command_line_assistant.dbus.structures.history import HistoryList
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

    def __init__(
        self, clear: bool, first: bool, last: bool, filter: Optional[str] = None
    ) -> None:
        """Constructor of the class.

        Note:
            If none of the above is specified, the command will retrieve all
            user history.

        Args:
            clear (bool): If the history should be cleared
            first (bool): Retrieve only the first conversation from history
            last (bool): Retrieve only last conversation from history
            filter (Optional[str], optional): Keyword to filter in the user history
        """
        self._clear = clear
        self._first = first
        self._last = last
        self._filter = filter

        self._proxy = HISTORY_IDENTIFIER.get_proxy()
        self._user_proxy = USER_IDENTIFIER.get_proxy()
        self._chat_proxy = CHAT_IDENTIFIER.get_proxy()

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
            user_id = self._user_proxy.GetUserId(self._context.effective_user_id)

            if self._clear:
                self._clear_history(user_id)
            elif self._first:
                self._retrieve_first_conversation(user_id)
            elif self._last:
                self._retrieve_last_conversation(user_id)
            elif self._filter:
                self._retrieve_conversation_filtered(user_id, self._filter)
            else:
                self._retrieve_all_conversations(user_id)

            return 0
        except (
            MissingHistoryFileError,
            CorruptedHistoryError,
            ChatNotFoundError,
            HistoryNotAvailable,
        ) as e:
            self._error_renderer.render(str(e))
            return 1

    def _retrieve_all_conversations(self, user_id: str) -> None:
        """Retrieve and display all conversations from history."""
        self._text_renderer.render("Getting all conversations from history.")
        response = self._proxy.GetHistory(user_id)
        history = HistoryList.from_structure(response)

        # Display the conversation
        self._show_history(history)

    def _retrieve_first_conversation(self, user_id: str) -> None:
        """Retrieve the first conversation in the conversation cache."""
        self._text_renderer.render("Getting first conversation from history.")
        response = self._proxy.GetFirstConversation(user_id)
        history = HistoryList.from_structure(response)

        # Display the conversation
        self._show_history(history)

    def _retrieve_conversation_filtered(self, user_id: str, filter: str) -> None:
        """Retrieve the user conversation with keyword filtering.

        Args:
            filter (str): Keyword to filter in the user history
        """
        self._text_renderer.render("Filtering conversation history.")
        response = self._proxy.GetFilteredConversation(user_id, filter)

        # Handle and display the response
        history = HistoryList.from_structure(response)

        # Display the conversation
        self._show_history(history)

    def _retrieve_last_conversation(self, user_id: str) -> None:
        """Retrieve the last conversation in the conversation cache."""
        self._text_renderer.render("Getting last conversation from history.")
        response = self._proxy.GetLastConversation(user_id)

        history = HistoryList.from_structure(response)
        # Display the conversation
        self._show_history(history)

    def _clear_history(self, user_id: str) -> None:
        """Clear the user history"""
        self._text_renderer.render("Cleaning the history.")
        self._proxy.ClearHistory(user_id)

    def _show_history(self, entries: HistoryList) -> None:
        """Internal method to show the history in a standardized way

        Args:
            entries (list[HistoryItem]): The list of entries in the history
        """
        is_separator_needed = len(entries.histories) > 1
        for entry in entries.histories:
            self._q_renderer.render(f"Question: {entry.question}")
            self._a_renderer.render(f"Answer: {entry.response}")

            timestamp = f"Time: {entry.created_at}"
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
        help="Manage user conversation history",
    )

    filtering_options = history_parser.add_argument_group("Filtering options")
    filtering_options.add_argument(
        "-f",
        "--first",
        action="store_true",
        help="Get the first conversation from history. If no --from is specified, this will get the first conversation across all chats.",
    )
    filtering_options.add_argument(
        "-l",
        "--last",
        action="store_true",
        help="Get the last conversation from history. If no --from is specified, this will get the last conversation across all chats.",
    )
    filtering_options.add_argument(
        "-fi",
        "--filter",
        help="Search for a specific keyword of text in the history. If no --from is specified, this will filter conversations across all chats.",
    )

    management_options = history_parser.add_argument_group("Management options")
    management_options.add_argument(
        "-c",
        "--clear",
        action="store_true",
        help="Clear the entire history. If no --from is specified, it will clear all history from all chats.",
    )

    history_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> HistoryCommand:
    """Internal command factory to create the command class

    Args:
        args (Namespace): The arguments processed with argparse.

    Returns:
        HistoryCommand: Return an instance of class
    """
    return HistoryCommand(args.clear, args.first, args.last, args.filter)
