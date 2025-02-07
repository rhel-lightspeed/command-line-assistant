"""Module to handle the history command."""

from argparse import Namespace
from dataclasses import dataclass
from enum import auto
from typing import ClassVar

from command_line_assistant.commands.base import (
    BaseOperation,
    CommandOperationFactory,
    CommandOperationType,
)
from command_line_assistant.dbus.constants import (
    CHAT_IDENTIFIER,
    HISTORY_IDENTIFIER,
    USER_IDENTIFIER,
)
from command_line_assistant.dbus.structures.history import HistoryList
from command_line_assistant.exceptions import HistoryCommandException
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import (
    BaseCLICommand,
    SubParsersAction,
    create_subparser,
)
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_text_renderer,
)


class HistoryOperationType(CommandOperationType):
    CLEAR = auto()
    FIRST = auto()
    LAST = auto()
    FILTER = auto()
    ALL = auto()


class HistoryOperationFactory(CommandOperationFactory):
    """Factory for creating shell operations with decorator-based registration"""

    # Mapping of CLI arguments to operation types
    _arg_to_operation: ClassVar[dict[str, CommandOperationType]] = {
        "clear": HistoryOperationType.CLEAR,
        "first": HistoryOperationType.FIRST,
        "last": HistoryOperationType.LAST,
        "filter": HistoryOperationType.FILTER,
    }


@dataclass
class BaseHistoryOperation(BaseOperation):
    chat_proxy = CHAT_IDENTIFIER.get_proxy()
    history_proxy = HISTORY_IDENTIFIER.get_proxy()
    user_proxy = USER_IDENTIFIER.get_proxy()

    q_renderer: TextRenderer = create_text_renderer(
        decorators=[ColorDecorator("lightgreen")]
    )
    a_renderer: TextRenderer = create_text_renderer(
        decorators=[ColorDecorator("lightblue")]
    )

    def _show_history(self, entries: HistoryList) -> None:
        """Internal method to show the history in a standardized way

        Args:
            entries (list[HistoryItem]): The list of entries in the history
        """
        is_separator_needed = len(entries.histories) > 1
        for entry in entries.histories:
            self.q_renderer.render(f"Question: {entry.question}")
            self.a_renderer.render(f"Answer: {entry.response}")

            timestamp = f"Time: {entry.created_at}"
            self.text_renderer.render(timestamp)

            if is_separator_needed:
                # Separator between conversations
                self.text_renderer.render("-" * len(timestamp))


@HistoryOperationFactory.register(HistoryOperationType.CLEAR)
class ClearHistoryOperation(BaseHistoryOperation):
    def execute(self) -> None:
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        self.text_renderer.render("Cleaning the history.")
        self.history_proxy.ClearHistory(user_id)


@HistoryOperationFactory.register(HistoryOperationType.FIRST)
class FirstHistoryOperation(BaseHistoryOperation):
    def execute(self) -> None:
        self.text_renderer.render("Getting first conversation from history.")
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        response = self.history_proxy.GetFirstConversation(user_id)
        history = HistoryList.from_structure(response)

        # Display the conversation
        self._show_history(history)


@HistoryOperationFactory.register(HistoryOperationType.LAST)
class LastHistoryOperation(BaseHistoryOperation):
    def execute(self) -> None:
        self.text_renderer.render("Getting last conversation from history.")
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        response = self.history_proxy.GetLastConversation(user_id)

        history = HistoryList.from_structure(response)
        # Display the conversation
        self._show_history(history)


@HistoryOperationFactory.register(HistoryOperationType.FILTER)
class FilteredHistoryOperation(BaseHistoryOperation):
    def execute(self) -> None:
        self.text_renderer.render("Filtering conversation history.")
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        response = self.history_proxy.GetFilteredConversation(user_id, filter)

        # Handle and display the response
        history = HistoryList.from_structure(response)

        # Display the conversation
        self._show_history(history)


@HistoryOperationFactory.register(HistoryOperationType.ALL)
class AllHistoryOperation(BaseHistoryOperation):
    def execute(self) -> None:
        self.text_renderer.render("Getting all conversations from history.")
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        response = self.history_proxy.GetHistory(user_id)
        history = HistoryList.from_structure(response)

        # Display the conversation
        self._show_history(history)


class HistoryCommand(BaseCLICommand):
    """Class that represents the history command."""

    def __init__(self, args: Namespace) -> None:
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
        self._args = args

        self._error_renderer: TextRenderer = create_error_renderer()

        self._operation_factory = HistoryOperationFactory()

        super().__init__()

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Status code of the execution.
        """
        try:
            operation = self._operation_factory.create_operation(
                self._args, self._context
            )
            if operation:
                operation.execute()
            return 0
        except HistoryCommandException as e:
            self._error_renderer.render(str(e))
            return 1


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the root parser.

    Args:
        parser (SubParsersAction): Root parser to register command-specific arguments
    """
    history_parser = create_subparser(parser, "history", "Manage conversation history")

    filtering_options = history_parser.add_argument_group("Filtering Options")
    filtering_options.add_argument(
        "-f",
        "--first",
        action="store_true",
        help="Get the first conversation from history.",
    )
    filtering_options.add_argument(
        "-l",
        "--last",
        action="store_true",
        help="Get the last conversation from history.",
    )
    filtering_options.add_argument(
        "-fi",
        "--filter",
        help="Search for a specific keyword of text in the history.",
    )
    filtering_options.add_argument(
        "-a", "--all", action="store_true", help="Get all conversation from history."
    )

    management_options = history_parser.add_argument_group("Management Options")
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
    return HistoryCommand(args)
