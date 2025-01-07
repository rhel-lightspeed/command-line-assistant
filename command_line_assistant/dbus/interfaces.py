"""D-Bus interfaces that defines and powers our commands."""

import logging

from dasbus.server.interface import dbus_interface
from dasbus.server.property import emits_properties_changed
from dasbus.server.template import InterfaceTemplate
from dasbus.typing import Str, Structure

from command_line_assistant.daemon.http.query import submit
from command_line_assistant.dbus.constants import HISTORY_IDENTIFIER, QUERY_IDENTIFIER
from command_line_assistant.dbus.structures import (
    HistoryEntry,
    Message,
)
from command_line_assistant.history.manager import HistoryManager
from command_line_assistant.history.plugins.local import LocalHistory

audit_logger = logging.getLogger("audit")
logger = logging.getLogger(__name__)


@dbus_interface(QUERY_IDENTIFIER.interface_name)
class QueryInterface(InterfaceTemplate):
    """The DBus interface of a query."""

    def RetrieveAnswer(self) -> Structure:
        """This method is mainly called by the client to retrieve it's answer.

        Returns:
            Structure: The message output in format of a d-bus structure.
        """
        query = self.implementation.query.message
        user = self.implementation.query.user

        # Submit query to backend
        llm_response = submit(query, self.implementation.config)

        # Create message object
        message = Message()
        message.message = llm_response

        # Deal with history management
        manager = HistoryManager(self.implementation.config, LocalHistory)
        current_history = manager.read()
        manager.write(current_history, query, llm_response)

        audit_logger.info(
            "Query executed successfully.",
            extra={
                "user": user,
                "query": query,
                "response": llm_response,
            },
        )
        # Return the data - okay
        return Message.to_structure(message)

    @emits_properties_changed
    def ProcessQuery(self, query: Structure) -> None:
        """Process a given query by the user

        Args:
            query (Structure): The user query
        """
        self.implementation.process_query(Message.from_structure(query))


@dbus_interface(HISTORY_IDENTIFIER.interface_name)
class HistoryInterface(InterfaceTemplate):
    """The DBus interface of a history"""

    def GetHistory(self) -> Structure:
        """Get all conversations from history.

        Returns:
            Structure: The history entries in a dbus structure format.
        """
        manager = HistoryManager(self.implementation.config, LocalHistory)
        history = manager.read()

        history_entry = HistoryEntry()
        if history.history:
            _ = [
                history_entry.set_from_dict(entry.to_dict())
                for entry in history.history
            ]
        else:
            history_entry.entries = []

        return HistoryEntry.to_structure(history_entry)

    # Add new methods with parameters
    def GetFirstConversation(self) -> Structure:
        """Get first conversation from history.

        Returns:
            Structure: A single history entry in a dbus structure format.
        """
        manager = HistoryManager(self.implementation.config, LocalHistory)
        history = manager.read()
        history_entry = HistoryEntry()
        if history.history:
            last_entry = history.history[0]
            history_entry.set_from_dict(last_entry.to_dict())

        return HistoryEntry.to_structure(history_entry)

    def GetLastConversation(self) -> Structure:
        """Get last conversation from history.

        Returns:
            Structure: A single history entyr in a dbus structure format.
        """
        manager = HistoryManager(self.implementation.config, LocalHistory)
        history = manager.read()
        history_entry = HistoryEntry()

        if history.history:
            last_entry = history.history[-1]
            history_entry.set_from_dict(last_entry.to_dict())

        return HistoryEntry.to_structure(history_entry)

    def GetFilteredConversation(self, filter: Str) -> Structure:
        """Get last conversation from history.

        Args:
            filter (str): The filter

        Returns:
            Structure: A single history entyr in a dbus structure format.
        """
        manager = HistoryManager(self.implementation.config, LocalHistory)
        history = manager.read()
        history_entry = HistoryEntry()
        found_entries = []

        if history.history:
            logger.info("Filtering the user history with keyword '%s'", filter)
            # We ignore the type in the condition as pyright thinks that "Str" is not "str".
            # Pyright is correct about this, but "Str" is a special type for dbus. It will be "str" in the end.
            found_entries = [
                entry
                for entry in history.history
                if (
                    filter in entry.interaction.query.text  # type: ignore
                    or filter in entry.interaction.response.text  # type: ignore
                )
            ]

        logger.info("Found %s entries in the history", len(found_entries))
        # Normalize the entries to send over dbus
        _ = [
            history_entry.set_from_dict(entry.to_dict()) for entry in set(found_entries)
        ]
        return HistoryEntry.to_structure(history_entry)

    def ClearHistory(self) -> None:
        """Clear the user history."""
        manager = HistoryManager(self.implementation.config, LocalHistory)
        manager.clear()
