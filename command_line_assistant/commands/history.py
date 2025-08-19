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
from command_line_assistant.rendering.colors import Color, colorize
from command_line_assistant.rendering.formatting import wrap
from command_line_assistant.rendering.markdown import markdown_to_ansi
from command_line_assistant.utils.cli import (
    CommandContext,
    SubParsersAction,
    create_subparser,
)
from command_line_assistant.utils.renderers import (
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
    """

    def __init__(
        self,
        args: Namespace,
        context: CommandContext,
        chat_proxy: ChatInterface,
        history_proxy: HistoryInterface,
        user_proxy: UserInterface,
    ):
        """Constructor of the class.

        Arguments:
            args (Namespace): The arguments from CLI
            context (CommandContext): Context for the commands
            chat_proxy (ChatInterface): The proxy object for dbus chat
            history_proxy (HistoryInterface): The proxy object for dbus history
            user_proxy (HistoryInterface): The proxy object for dbus user
        """
        super().__init__(
            args,
            context,
            chat_proxy,
            history_proxy,
            user_proxy,
        )

    def _show_history(self, entries: HistoryList) -> None:
        """Internal method to show the history in a standardized way

        Arguments:
            entries (HistoryItem): The list of entries in the history
        """
        if not entries.histories:
            self.write_line("No history entries found")
            return

        for entry in entries.histories:
            # Render question block
            question_text = f"## 🤔 Question\n{entry.question}"
            self.write_question_line(question_text)

            # Add a small spacing
            self.write_line("")

            # Render answer block
            answer_text = f"## 🤖 Answer\n{entry.response}"
            self.write_answer_line(answer_text)

            from_chat_message = f"\n*From chat: {entry.chat_name}*"
            self.write_metadata_line(from_chat_message)

            created_at_message = f"*Created at: {format_datetime(entry.created_at)}*"
            self.write_metadata_line(created_at_message)
            # Add separator between entries if needed
            if len(entries.histories) > 1:
                self.write_line("\n" + "═" * (len(created_at_message) - 1) + "\n")

    def write_question_line(self, question: str) -> None:
        """Write the question line to the stream."""
        self._stdout_stream.add_line_chunk(wrap(colorize(question, Color.CYAN)))

    def write_answer_line(self, answer: str) -> None:
        """Write the answer line to the stream."""
        self._stdout_stream.add_line_chunk(wrap(markdown_to_ansi(answer)))

    def write_metadata_line(self, metadata: str) -> None:
        """Write the metadata line to the stream."""
        self._stdout_stream.add_line_chunk(wrap(colorize(metadata, Color.YELLOW)))


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
            self.write_line("Cleaning the history.")
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
            self.write_line("Cleaning the history.")
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
            self.write_line("Getting first conversation from history.")
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
            self.write_line("Getting last conversation from history.")
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
            self.write_line("Filtering conversation history.")
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
            self.write_line("Getting all conversations from history.")
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
        operation_factory = HistoryOperationFactory()
        try:
            operation = operation_factory.create_operation(self._args, self._context)

            if operation:
                operation.execute()
            return 0
        except HistoryCommandException as e:
            logger.info("Failed to execute history command: %s", str(e))
            self.write_error_line(str(e))
            return e.code


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
        "-a", "--all", action="store_true", help="Get all the conversation history."
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
    if not (args.last or args.first or args.filter):
        args.all = True

    return HistoryCommand(args)
