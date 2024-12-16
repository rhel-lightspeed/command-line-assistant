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
from command_line_assistant.history import handle_history_read, handle_history_write


@dbus_interface(QUERY_IDENTIFIER.interface_name)
class QueryInterface(InterfaceTemplate):
    """The DBus interface of a query."""

    def connect_signals(self) -> None:
        """Connect the signals."""
        # Watch for property changes based on the query_changed method.
        self.watch_property("RetrieveAnswer", self.implementation.query_changed)

    @property
    def RetrieveAnswer(self) -> Structure:
        """This method is mainly called by the client to retrieve it's answer."""
        output = Message()
        llm_response = submit(
            self.implementation.query.message, self.implementation.config
        )
        print("llm_response", llm_response)
        output.message = llm_response
        return Message.to_structure(output)

    @emits_properties_changed
    def ProcessQuery(self, query: Structure) -> None:
        """Process the given query."""
        self.implementation.process_query(Message.from_structure(query))


@dbus_interface(HISTORY_IDENTIFIER.interface_name)
class HistoryInterface(InterfaceTemplate):
    @property
    def GetHistory(self) -> Structure:
        history = HistoryEntry()
        history.entries = handle_history_read(self.implementation.config)
        return history.to_structure(history)

    def ClearHistory(self) -> None:
        handle_history_write(self.implementation.config.history.file, [], "")
