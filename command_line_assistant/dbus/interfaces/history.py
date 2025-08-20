"""D-Bus interfaces that defines and powers our commands."""

import logging

from dasbus.server.interface import dbus_interface
from dasbus.server.template import InterfaceTemplate
from dasbus.typing import Str, Structure

from command_line_assistant.daemon.database.models.history import (
    HistoryModel,
    InteractionModel,
)
from command_line_assistant.dbus.constants import HISTORY_IDENTIFIER
from command_line_assistant.dbus.context import DaemonContext
from command_line_assistant.dbus.exceptions import (
    HistoryNotAvailableError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.structures.history import (
    HistoryEntry,
    HistoryList,
)
from command_line_assistant.history.manager import HistoryManager
from command_line_assistant.history.plugins.local import LocalHistory

logger = logging.getLogger(__name__)


#: Default message in case a history chat is not available.
HISTORY_NOT_AVAILABLE_MESSAGE = (
    "Looks like no history was found. Try asking something first!"
)
HISTORY_NOT_ENABLED_MESSAGE = (
    "Looks like history is not enabled yet. Enable it in the configuration "
    "file before trying to access history."
)


@dbus_interface(HISTORY_IDENTIFIER.interface_name)
class HistoryInterface(InterfaceTemplate):
    """The DBus interface of a history"""

    def __init__(self, implementation: DaemonContext) -> None:
        """Constructor of the class

        Arguments:
            implementation (DaemonContext): The implementation context to be used in an interface.
        """
        super().__init__(implementation)

        self._history_manager = HistoryManager(implementation.config, LocalHistory)

    def GetHistory(self, user_id: Str) -> Structure:
        """Get all conversations from history.

        Arguments:
            user_id (Str): The identifier of the user.

        Returns:
            Structure: The history entries in a dbus structure format.
        """
        if not self._history_manager.is_history_enabled:
            raise HistoryNotEnabledError(HISTORY_NOT_ENABLED_MESSAGE)

        logger.info("Getting all history data from user '%s'", user_id)
        history_entries = self._history_manager.read(user_id)

        if not history_entries:
            raise HistoryNotAvailableError(HISTORY_NOT_AVAILABLE_MESSAGE)

        history_entry = _parse_interactions(history_entries)
        return history_entry.structure()

    # Add new methods with parameters
    def GetFirstConversation(self, user_id: Str, from_chat: Str) -> Structure:
        """Get first conversation from history.

        Arguments:
            user_id (Str): The identifier of the user.
            from_chat (Str): Chat name identifier

        Returns:
            Structure: A single history entry in a dbus structure format.
        """
        if not self._history_manager.is_history_enabled:
            raise HistoryNotEnabledError(HISTORY_NOT_ENABLED_MESSAGE)

        logger.info(
            "Getting the first history log for user '%s' in chat '%s'",
            user_id,
            from_chat,
        )
        history_entries = self._history_manager.read_from_chat(user_id, from_chat)

        if not history_entries:
            raise HistoryNotAvailableError(HISTORY_NOT_AVAILABLE_MESSAGE)

        history_entries.interactions = history_entries.interactions[:1]  # type: ignore
        history_entry = _parse_interactions([history_entries])  # type: ignore
        return history_entry.structure()

    def GetLastConversation(self, user_id: Str, from_chat: Str) -> Structure:
        """Get last conversation from history.

        Arguments:
            user_id (Str): The identifier of the user.
            from_chat (Str): Chat name identifier

        Raises:
            HistoryNotEnabledError: If history is not enabled.
            HistoryNotAvailableError: If no history is available for the user.

        Returns:
            Structure: A single history entyr in a dbus structure format.
        """
        if not self._history_manager.is_history_enabled:
            raise HistoryNotEnabledError(HISTORY_NOT_ENABLED_MESSAGE)

        logger.info(
            "Get the most recent history for user '%s' in chat '%s'", user_id, from_chat
        )
        history_entries = self._history_manager.read_from_chat(user_id, from_chat)

        if not history_entries:
            raise HistoryNotAvailableError(HISTORY_NOT_AVAILABLE_MESSAGE)

        history_entries.interactions = history_entries.interactions[-1:]  # type: ignore
        history_entry = _parse_interactions([history_entries])  # type: ignore
        return history_entry.structure()

    def GetFilteredConversation(
        self, user_id: Str, filter: Str, from_chat: Str
    ) -> Structure:
        """Get last conversation from history.

        Arguments:
            user_id (Str): The identifier of the user.
            filter (str): The filter
            from_chat (Str): Chat name identifier

        Returns:
            Structure: Structure of history entries.
        """
        if not self._history_manager.is_history_enabled:
            raise HistoryNotEnabledError(HISTORY_NOT_ENABLED_MESSAGE)

        history_entries = self._history_manager.read_from_chat(user_id, from_chat)

        if not history_entries:
            raise HistoryNotAvailableError(HISTORY_NOT_AVAILABLE_MESSAGE)

        logger.info(
            "Filtering the user history with keyword '%s' for user '%s' in chat '%s'",
            filter,
            user_id,
            from_chat,
        )
        filtered_entries = _filter_history_with_keyword([history_entries], filter)  # type: ignore
        history_entries.interactions = filtered_entries  # type: ignore
        history_entry = _parse_interactions([history_entries])  # type: ignore
        return history_entry.structure()

    def ClearAllHistory(self, user_id: Str) -> None:
        """Clear the user history.

        Arguments:
            user_id (Str): The identifier of the user.
        """
        if not self._history_manager.is_history_enabled:
            raise HistoryNotEnabledError(HISTORY_NOT_ENABLED_MESSAGE)

        logger.info(
            "Clearing history entries for user.",
            extra={"audit": True, "user_id": user_id},
        )
        self._history_manager.clear(user_id)

    def ClearHistory(self, user_id: Str, from_chat: Str) -> None:
        """Clear the user history.

        Arguments:
            user_id (Str): The identifier of the user.
        """
        if not self._history_manager.is_history_enabled:
            raise HistoryNotEnabledError(HISTORY_NOT_ENABLED_MESSAGE)

        logger.info(
            "Clearing history entries for user.",
            extra={"audit": True, "user_id": user_id, "from_chat": from_chat},
        )
        self._history_manager.clear_from_chat(user_id, from_chat)

    def WriteHistory(
        self, chat_id: Str, user_id: Str, question: Str, response: Str
    ) -> None:
        """Write a new entry to the user history.

        Arguments:
            chat_id (Str): The identifier of the chat session.
            user_id (Str): The identifier of the user.
            question (Str): The question asked by the user.
            response (Str): The response given to the user.
        """
        if not self._history_manager.is_history_enabled:
            raise HistoryNotEnabledError(HISTORY_NOT_ENABLED_MESSAGE)

        self._history_manager.write(chat_id, user_id, question, response)
        logger.info(
            "Wrote a new entry to the user history for user.",
            extra={"audit": True, "user_id": user_id, "chat_id": str(chat_id)},
        )


def _parse_interactions(histories: list[HistoryModel]) -> HistoryList:
    """Parse the history interactions in a common format for all methods

    Arguments:
        histories (list[HistoryModel]): Histories fetched from the database.

    Returns:
        HistoryEntry: An instance of HistoryEntry with all necessary
        information.
    """

    # We type ignore both question and response because we know that it is str
    # being returned from the database. The exception of converting created_at
    # is because it returns in a datetime format. To avoid casting inside the
    # structures, we cast it to str here.
    #
    # Pyright can't implicit convert from Column[str] to str.
    history_entries = [
        HistoryEntry(
            interaction.question,  # type: ignore
            interaction.response,  # type: ignore
            history.chats.name,
            str(interaction.created_at),
        )
        for history in histories
        for interaction in history.interactions
    ]
    return HistoryList(histories=history_entries)


def _filter_history_with_keyword(
    entries: list[HistoryModel], keyword: str
) -> list[InteractionModel]:
    """Filter the history entries based on keyword.

    Arguments:
        entries (list[HistoryModel]): The list of entries returned from the database
        keyword (str): The keyword to filter.

    Returns:
        list[InteractionModel]: Filtered results.
    """
    # Filter entries where the query or response contains the filter string
    return [
        interaction
        for entry in entries
        for interaction in entry.interactions
        if (keyword in interaction.question or keyword in interaction.response)
    ]
