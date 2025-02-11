"""Module to handle the history command."""

from argparse import Namespace
from enum import auto
from typing import ClassVar

from command_line_assistant.commands.base import (
    BaseCLICommand,
    BaseOperation,
    CommandOperationFactory,
    CommandOperationType,
)
from command_line_assistant.dbus.interfaces.chat import ChatInterface
from command_line_assistant.dbus.interfaces.history import HistoryInterface
from command_line_assistant.dbus.interfaces.user import UserInterface
from command_line_assistant.dbus.structures.history import HistoryList
from command_line_assistant.exceptions import HistoryCommandException
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import (
    CommandContext,
    SubParsersAction,
    create_subparser,
)
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_text_renderer,
)


class HistoryOperationType(CommandOperationType):
    """Enum to control the operations for the command"""

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


class BaseHistoryOperation(BaseOperation):
    """Base history operation common to all operations

    Warning:
        The proxy attributes in this class are not really mapping to interface.
        It maps to internal dasbus ObjectProxy, but to avoid pyright syntax
        errors, we type then as their respective interfaces. The objective of
        the `ObjectProxy` is to serve as a proxy for the real interfaces.

    Attributes:
        q_renderer (TextRenderer): Instance of a text renderer to render questions
        a_renderer (TextRenderer): Instance of a text renderer to render answers
    """

    def __init__(
        self,
        text_renderer: TextRenderer,
        warning_renderer: TextRenderer,
        error_renderer: TextRenderer,
        args: Namespace,
        context: CommandContext,
        chat_proxy: ChatInterface,
        history_proxy: HistoryInterface,
        user_proxy: UserInterface,
    ):
        """Constructor of the class.

        Arguments:
            text_renderer (TextRenderer): Instance of text renderer class
            warning_renderer (TextRenderer): Instance of text renderer class
            error_renderer (TextRenderer): Instance of text renderer class
            args (Namespace): The arguments from CLI
            context (CommandContext): Context for the commands
            chat_proxy (ChatInterface): The proxy object for dbus chat
            history_proxy (HistoryInterface): The proxy object for dbus history
            user_proxy (HistoryInterface): The proxy object for dbus user
        """
        super().__init__(
            text_renderer,
            warning_renderer,
            error_renderer,
            args,
            context,
            chat_proxy,
            history_proxy,
            user_proxy,
        )

        self.q_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator("lightgreen")]
        )
        self.a_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator("lightblue")]
        )

    def _show_history(self, entries: HistoryList) -> None:
        """Internal method to show the history in a standardized way

        Arguments:
            entries (list[HistoryItem]): The list of entries in the history
        """
        if not entries.histories:
            self.text_renderer.render("No history entries found")
            return

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
    """Class to hold the clean operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        self.text_renderer.render("Cleaning the history.")
        self.history_proxy.ClearHistory(user_id)


@HistoryOperationFactory.register(HistoryOperationType.FIRST)
class FirstHistoryOperation(BaseHistoryOperation):
    """Class to hold the first history operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        self.text_renderer.render("Getting first conversation from history.")
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        response = self.history_proxy.GetFirstConversation(user_id)
        history = HistoryList.from_structure(response)

        # Display the conversation
        self._show_history(history)


@HistoryOperationFactory.register(HistoryOperationType.LAST)
class LastHistoryOperation(BaseHistoryOperation):
    """Class to hold the last history operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        self.text_renderer.render("Getting last conversation from history.")
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        response = self.history_proxy.GetLastConversation(user_id)

        history = HistoryList.from_structure(response)
        # Display the conversation
        self._show_history(history)


@HistoryOperationFactory.register(HistoryOperationType.FILTER)
class FilteredHistoryOperation(BaseHistoryOperation):
    """Class to hold the filtering history operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        self.text_renderer.render("Filtering conversation history.")
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        response = self.history_proxy.GetFilteredConversation(user_id, self.args.filter)

        # Handle and display the response
        history = HistoryList.from_structure(response)

        # Display the conversation
        self._show_history(history)


@HistoryOperationFactory.register(HistoryOperationType.ALL)
class AllHistoryOperation(BaseHistoryOperation):
    """Class to hold the reading of all history operation."""

    def execute(self) -> None:
        """Default method to execute the operation"""
        self.text_renderer.render("Getting all conversations from history.")
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        response = self.history_proxy.GetHistory(user_id)
        history = HistoryList.from_structure(response)

        # Display the conversation
        self._show_history(history)


class HistoryCommand(BaseCLICommand):
    """Class that represents the history command."""

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Status code of the execution.
        """
        error_renderer: TextRenderer = create_error_renderer()
        operation_factory = HistoryOperationFactory()
        try:
            operation = operation_factory.create_operation(
                self._args, self._context, error_renderer=error_renderer
            )
            if operation:
                operation.execute()
            return 0
        except HistoryCommandException as e:
            error_renderer.render(str(e))
            return 1


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the root parser.

    Arguments:
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

    Arguments:
        args (Namespace): The arguments processed with argparse.

    Returns:
        HistoryCommand: Return an instance of class
    """
    return HistoryCommand(args)
