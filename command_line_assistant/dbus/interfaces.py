"""D-Bus interfaces that defines and powers our commands."""

import logging

from dasbus.server.interface import dbus_interface
from dasbus.server.template import InterfaceTemplate
from dasbus.typing import Int, Str, Structure

from command_line_assistant.daemon.http.query import submit
from command_line_assistant.dbus.constants import CHAT_IDENTIFIER, HISTORY_IDENTIFIER
from command_line_assistant.dbus.structures import (
    HistoryEntry,
    HistoryItem,
    Message,
    MessageInput,
)
from command_line_assistant.history.manager import HistoryManager
from command_line_assistant.history.plugins.local import LocalHistory

audit_logger = logging.getLogger("audit")
logger = logging.getLogger(__name__)


@dbus_interface(CHAT_IDENTIFIER.interface_name)
class ChatInterface(InterfaceTemplate):
    """The DBus interface of a query."""

    def AskQuestion(self, message_input: Structure) -> Structure:
        """This method is mainly called by the client to retrieve it's answer.

        Returns:
            Structure: The message output in format of a d-bus structure.
        """
        content = MessageInput.from_structure(message_input)
        # Submit query to backend
        data = {
            "question": content.question,
            "context": {
                "stdin": content.stdin,
                "attachments": {
                    "contents": content.attachment_contents,
                    "mimetype": content.attachment_mimetype,
                },
            },
        }
        llm_response = submit(data, self.implementation.config)

        # Create message object
        message = Message()
        message.message = llm_response

        # Deal with history management
        manager = HistoryManager(self.implementation.config, content.user, LocalHistory)
        manager.write(content.question, llm_response)

        audit_logger.info(
            "Query executed successfully.",
            extra={
                "user": content.user,
                "query": content.question,
                "response": llm_response,
            },
        )
        # Return the data
        return Message.to_structure(message)


@dbus_interface(HISTORY_IDENTIFIER.interface_name)
class HistoryInterface(InterfaceTemplate):
    """The DBus interface of a history"""

    def GetHistory(self, effective_user_id: Int) -> Structure:
        """Get all conversations from history.

        Returns:
            Structure: The history entries in a dbus structure format.
        """
        manager = HistoryManager(
            self.implementation.config, effective_user_id, LocalHistory
        )
        history_entries = manager.read()
        history_entry = HistoryEntry()

        if history_entries:
            history_entry = _parse_history_entries(history_entries)

        return HistoryEntry.to_structure(history_entry)

    # Add new methods with parameters
    def GetFirstConversation(self, effective_user_id: Int) -> Structure:
        """Get first conversation from history.

        Returns:
            Structure: A single history entry in a dbus structure format.
        """
        manager = HistoryManager(
            self.implementation.config, effective_user_id, LocalHistory
        )
        history_entries = manager.read()
        history_entry = HistoryEntry()

        if history_entries:
            history_entry = _parse_history_entries(history_entries[:1])

        return HistoryEntry.to_structure(history_entry)

    def GetLastConversation(self, effective_user_id: Int) -> Structure:
        """Get last conversation from history.

        Returns:
            Structure: A single history entyr in a dbus structure format.
        """
        manager = HistoryManager(
            self.implementation.config, effective_user_id, LocalHistory
        )
        history_entries = manager.read()
        history_entry = HistoryEntry()

        if history_entries:
            history_entry = _parse_history_entries(history_entries[-1:])

        return HistoryEntry.to_structure(history_entry)

    def GetFilteredConversation(self, effective_user_id: Int, filter: Str) -> Structure:
        """Get last conversation from history.

        Args:
            filter (str): The filter

        Returns:
            Structure: A single history entyr in a dbus structure format.
        """
        manager = HistoryManager(
            self.implementation.config, effective_user_id, LocalHistory
        )
        history_entries = manager.read()
        history_entry = HistoryEntry()

        if history_entries:
            logger.info("Filtering the user history with keyword '%s'", filter)
            # Filter entries where the query or response contains the filter string
            filtered_entries = [
                entry
                for entry in history_entries
                if (filter in entry["query"] or filter in entry["response"])
            ]

            history_entry = _parse_history_entries(filtered_entries)

        return HistoryEntry.to_structure(history_entry)

    def ClearHistory(self, effective_user_id: Int) -> None:
        """Clear the user history."""
        manager = HistoryManager(
            self.implementation.config, effective_user_id, LocalHistory
        )
        manager.clear()


def _parse_history_entries(entries: list[dict[str, str]]) -> HistoryEntry:
    """Parse the history entries in a common format for all methods

    Args:
        entries (list[dict[str, str]]): List of entries in a dictionary format
        with only the necessary information.

    Returns:
        HistoryEntry: An instance of HistoryEntry with all necessary
        information.
    """
    history_entry = HistoryEntry()
    for entry in entries:
        history_item = HistoryItem()
        history_item.query = entry["query"]
        history_item.response = entry["response"]
        history_item.timestamp = entry["timestamp"]
        history_entry.entries.append(history_item)

    return history_entry
