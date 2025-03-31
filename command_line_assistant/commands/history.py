"""Module to handle the history command."""

import logging
from argparse import Namespace
from enum import auto
from typing import ClassVar

from command_line_assistant.commands.base import (
    BaseCLICommand,
    BaseOperation,
    CommandOperationFactory,
    CommandOperationType,
)
from command_line_assistant.dbus.exceptions import (
    HistoryNotAvailableError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.interfaces.chat import ChatInterface
from command_line_assistant.dbus.interfaces.history import HistoryInterface
from command_line_assistant.dbus.interfaces.user import UserInterface
from command_line_assistant.dbus.structures.chat import ChatList
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
    create_markdown_renderer,
    create_text_renderer,
    format_datetime,
)

logger = logging.getLogger(__name__)


#: Message for when the history is not available yet.
HISTORY_NOT_AVAILABLE_MESSAGE = (
    "Looks like no history was found. Try asking something first!"
)

#: Message for when the history is not enabled yet.
HISTORY_NOT_ENABLED_MESSAGE = "Looks like history is not enabled yet. Enable it in the configuration file before trying to access history."

#: History not enabled debug message.
HISTORY_NOT_ENABLED_DEBUG = "History is not enabled. Nothing to do."


class HistoryOperationType(CommandOperationType):
    """Enum to control the operations for the command"""

    CLEAR = auto()
    CLEAR_ALL = auto()
    FIRST = auto()
    LAST = auto()
    FILTER = auto()
    ALL = auto()


class HistoryOperationFactory(CommandOperationFactory):
    """Factory for creating shell operations with decorator-based registration"""

    # Mapping of CLI arguments to operation types
    _arg_to_operation: ClassVar[dict[str, CommandOperationType]] = {
        "clear": HistoryOperationType.CLEAR,
        "clear_all": HistoryOperationType.CLEAR_ALL,
        "first": HistoryOperationType.FIRST,
        "last": HistoryOperationType.LAST,
        "filter": HistoryOperationType.FILTER,
        "all": HistoryOperationType.ALL,
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
        # Add markdown renderer as a standard renderer
        self.markdown_renderer = create_markdown_renderer()

    def _show_history(self, entries: HistoryList) -> None:
        """Internal method to show the history in a standardized way

        Arguments:
            entries (HistoryItem): The list of entries in the history
        """
        if not entries.histories:
            self.text_renderer.render("No history entries found")
            return

        # Create specialized renderers for different parts
        question_renderer = create_markdown_renderer(
            decorators=[
                ColorDecorator(foreground="cyan"),
            ]
        )

        answer_renderer = create_markdown_renderer(
            decorators=[
                ColorDecorator(foreground="green"),
            ]
        )

        metadata_renderer = create_text_renderer(
            decorators=[
                ColorDecorator(foreground="yellow"),
            ]
        )

        for entry in entries.histories:
            # Render question block
            question_text = f"## 🤔 Question\n{entry.question}"
            question_renderer.render(question_text)

            # Add a small spacing
            self.text_renderer.render("")

            # Render answer block
            answer_text = f"## 🤖 Answer\n{entry.response}"
            answer_renderer.render(answer_text)

            from_chat_message = f"\n*From chat: {entry.chat_name}*"
            metadata_renderer.render(from_chat_message)

            created_at_message = f"*Created at: {format_datetime(entry.created_at)}*"
            metadata_renderer.render(created_at_message)
            # Add separator between entries if needed
            if len(entries.histories) > 1:
                self.text_renderer.render(
                    "\n" + "═" * (len(created_at_message) - 1) + "\n"
                )


@HistoryOperationFactory.register(HistoryOperationType.CLEAR)
class ClearHistoryOperation(BaseHistoryOperation):
    """Class to hold the clean operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        try:
            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            is_chat_available = self.chat_proxy.IsChatAvailable(
                user_id, self.args.from_chat
            )

            if not is_chat_available:
                raise HistoryCommandException(
                    "Nothing to clean as %s chat is not available."
                    % self.args.from_chat
                )

            self.history_proxy.ClearHistory(user_id, self.args.from_chat)
            self.text_renderer.render("Cleaning the history.")
        except HistoryNotAvailableError as e:
            logger.debug("Failed to clear the history: %s", str(e))
            raise HistoryCommandException(HISTORY_NOT_AVAILABLE_MESSAGE) from e
        except HistoryNotEnabledError as e:
            logger.debug(HISTORY_NOT_ENABLED_DEBUG)
            raise HistoryCommandException(HISTORY_NOT_ENABLED_MESSAGE) from e


@HistoryOperationFactory.register(HistoryOperationType.CLEAR_ALL)
class ClearAllHistoryOperation(BaseHistoryOperation):
    """Class to hold the clean operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        try:
            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            all_user_chats = ChatList.from_structure(
                self.chat_proxy.GetAllChatFromUser(user_id)
            )

            if not all_user_chats.chats:
                raise HistoryCommandException(
                    "Nothing to clean as there is no chat session in place."
                )

            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            self.text_renderer.render("Cleaning the history.")
            self.history_proxy.ClearAllHistory(user_id)
        except HistoryNotAvailableError as e:
            logger.debug("Failed to clear the history: %s", str(e))
            raise HistoryCommandException(HISTORY_NOT_AVAILABLE_MESSAGE) from e
        except HistoryNotEnabledError as e:
            logger.debug(HISTORY_NOT_ENABLED_DEBUG)
            raise HistoryCommandException(HISTORY_NOT_ENABLED_MESSAGE) from e


@HistoryOperationFactory.register(HistoryOperationType.FIRST)
class FirstHistoryOperation(BaseHistoryOperation):
    """Class to hold the first history operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        try:
            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            self.text_renderer.render("Getting first conversation from history.")
            response = self.history_proxy.GetFirstConversation(
                user_id, self.args.from_chat
            )
            history = HistoryList.from_structure(response)

            # Display the conversation
            self._show_history(history)
        except HistoryNotAvailableError as e:
            logger.debug("Failed to retrieve the first history entry: %s", str(e))
            raise HistoryCommandException(HISTORY_NOT_AVAILABLE_MESSAGE) from e
        except HistoryNotEnabledError as e:
            logger.debug(HISTORY_NOT_ENABLED_DEBUG)
            raise HistoryCommandException(HISTORY_NOT_ENABLED_MESSAGE) from e


@HistoryOperationFactory.register(HistoryOperationType.LAST)
class LastHistoryOperation(BaseHistoryOperation):
    """Class to hold the last history operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        try:
            self.text_renderer.render("Getting last conversation from history.")
            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            response = self.history_proxy.GetLastConversation(
                user_id, self.args.from_chat
            )

            history = HistoryList.from_structure(response)
            # Display the conversation
            self._show_history(history)
        except HistoryNotAvailableError as e:
            logger.debug("Failed to retrieve the last history entry: %s", str(e))
            raise HistoryCommandException(HISTORY_NOT_AVAILABLE_MESSAGE) from e
        except HistoryNotEnabledError as e:
            logger.debug(HISTORY_NOT_ENABLED_DEBUG)
            raise HistoryCommandException(HISTORY_NOT_ENABLED_MESSAGE) from e


@HistoryOperationFactory.register(HistoryOperationType.FILTER)
class FilteredHistoryOperation(BaseHistoryOperation):
    """Class to hold the filtering history operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        try:
            self.text_renderer.render("Filtering conversation history.")
            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            response = self.history_proxy.GetFilteredConversation(
                user_id, self.args.filter, self.args.from_chat
            )

            # Handle and display the response
            history = HistoryList.from_structure(response)

            # Display the conversation
            self._show_history(history)
        except HistoryNotAvailableError as e:
            logger.debug(
                "Failed to retrieve entries with filter '%s': %s",
                self.args.filter,
                str(e),
            )
            raise HistoryCommandException(HISTORY_NOT_AVAILABLE_MESSAGE) from e
        except HistoryNotEnabledError as e:
            logger.debug(HISTORY_NOT_ENABLED_DEBUG)
            raise HistoryCommandException(HISTORY_NOT_ENABLED_MESSAGE) from e


@HistoryOperationFactory.register(HistoryOperationType.ALL)
class AllHistoryOperation(BaseHistoryOperation):
    """Class to hold the reading of all history operation."""

    def execute(self) -> None:
        """Default method to execute the operation"""
        try:
            self.text_renderer.render("Getting all conversations from history.")
            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            response = self.history_proxy.GetHistory(user_id)
            history = HistoryList.from_structure(response)

            # Display the conversation
            self._show_history(history)
        except HistoryNotAvailableError as e:
            logger.debug("Failed to retrieve the all history entries: %s", str(e))
            raise HistoryCommandException(HISTORY_NOT_AVAILABLE_MESSAGE) from e
        except HistoryNotEnabledError as e:
            logger.debug(HISTORY_NOT_ENABLED_DEBUG)
            raise HistoryCommandException(HISTORY_NOT_ENABLED_MESSAGE) from e


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
    history_parser = create_subparser(parser, "history", "Manage Conversation History")

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
    filtering_options.add_argument(
        "--from-chat",
        help="Specify from which chat we should retrieve the history. Default chat is 'default'",
        default="default",
    )

    management_options = history_parser.add_argument_group("Management Options")
    management_options.add_argument(
        "-c",
        "--clear",
        action="store_true",
        help="Clear the entire history for a given chat. Use --from-chat with its given name to clear that particular history.",
    )
    management_options.add_argument(
        "--clear-all",
        action="store_true",
        help="Clear the entire history.",
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
