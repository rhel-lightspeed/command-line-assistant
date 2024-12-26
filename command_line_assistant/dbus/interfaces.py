from dasbus.server.interface import dbus_interface
from dasbus.server.property import emits_properties_changed
from dasbus.server.template import InterfaceTemplate
from dasbus.typing import Structure

from command_line_assistant.daemon.http.query import submit
from command_line_assistant.dbus.constants import HISTORY_IDENTIFIER, QUERY_IDENTIFIER
from command_line_assistant.dbus.structures import (
    HistoryEntry,
    Message,
)
from command_line_assistant.history.manager import HistoryManager
from command_line_assistant.history.plugins.local import LocalHistory


@dbus_interface(QUERY_IDENTIFIER.interface_name)
class QueryInterface(InterfaceTemplate):
    """The DBus interface of a query."""

    def RetrieveAnswer(self) -> Structure:
        """This method is mainly called by the client to retrieve it's answer."""
        query = self.implementation.query.message

        # Submit query to backend
        llm_response = submit(query, self.implementation.config)

        # Create message object
        message = Message()
        message.message = llm_response

        # Deal with history management
        manager = HistoryManager(self.implementation.config, LocalHistory)
        current_history = manager.read()
        manager.write(current_history, query, llm_response)

        # Return the data - okay
        return Message.to_structure(message)

    @emits_properties_changed
    def ProcessQuery(self, query: Structure) -> None:
        """Process the given query."""
        self.implementation.process_query(Message.from_structure(query))


@dbus_interface(HISTORY_IDENTIFIER.interface_name)
class HistoryInterface(InterfaceTemplate):
    def GetHistory(self) -> Structure:
        """Get all conversations from history."""
        manager = HistoryManager(self.implementation.config, LocalHistory)
        history = manager.read()

        history_entry = HistoryEntry()
        if history.history:
            [history_entry.set_from_dict(entry.to_dict()) for entry in history.history]
        else:
            history_entry.entries = []

        return HistoryEntry.to_structure(history_entry)

    # Add new methods with parameters
    def GetFirstConversation(self) -> Structure:
        """Get first conversation from history."""
        manager = HistoryManager(self.implementation.config, LocalHistory)
        history = manager.read()
        history_entry = HistoryEntry()
        if history.history:
            last_entry = history.history[0]
            history_entry.set_from_dict(last_entry.to_dict())

        return HistoryEntry.to_structure(history_entry)

    def GetLastConversation(self) -> Structure:
        """Get last conversation from history."""
        manager = HistoryManager(self.implementation.config, LocalHistory)
        history = manager.read()
        history_entry = HistoryEntry()

        if history.history:
            last_entry = history.history[-1]
            history_entry.set_from_dict(last_entry.to_dict())

        return HistoryEntry.to_structure(history_entry)

    def ClearHistory(self) -> None:
        manager = HistoryManager(self.implementation.config, LocalHistory)
        manager.clear()
