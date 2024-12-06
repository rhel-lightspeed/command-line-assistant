from typing import Optional

from dasbus.server.interface import dbus_interface
from dasbus.server.property import emits_properties_changed
from dasbus.server.template import InterfaceTemplate
from dasbus.signal import Signal
from dasbus.structure import DBusData
from dasbus.typing import Str, Structure

from command_line_assistant.config import Config
from command_line_assistant.daemon.http.query import submit
from command_line_assistant.dbus.constants import SERVICE_IDENTIFIER


class MessageInput(DBusData):
    """The message input from received from the client"""

    def __init__(self) -> None:
        self._message: Str = ""
        super().__init__()

    @property
    def message(self) -> Str:
        return self._message

    @message.setter
    def message(self, value: Str) -> None:
        self._message = value


class MessageOutput(DBusData):
    """The message output that will be sent to the client"""

    def __init__(self) -> None:
        self._message: Str = ""
        super().__init__()

    @property
    def message(self) -> Str:
        return self._message

    @message.setter
    def message(self, value: Str) -> None:
        self._message = value


@dbus_interface(SERVICE_IDENTIFIER.interface_name)
class QueryInterface(InterfaceTemplate):
    """The DBus interface of a query."""

    def connect_signals(self) -> None:
        """Connect the signals."""
        # Watch for property changes based on the query_changed method.
        self.watch_property("RetrieveAnswer", self.implementation.query_changed)

    @property
    def RetrieveAnswer(self) -> Structure:
        """This method is mainly called by the client to retrieve it's answer."""
        output = MessageOutput()
        llm_response = submit(
            self.implementation.query.message, self.implementation.config
        )
        output.message = llm_response
        return output.to_structure(output)

    @emits_properties_changed
    def ProcessQuery(self, query: Structure) -> None:
        """Process the given query."""
        self.implementation.process_query(MessageInput.from_structure(query))


class ProcessContext:
    """This is the process context that will handle anything query related"""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._input_query: Optional[MessageInput] = None
        self._query_changed = Signal()

    @property
    def config(self) -> Config:
        """Return the configuration from this context."""
        return self._config

    @property
    def query(self) -> Optional[MessageInput]:
        """Make it accessible publicly"""
        return self._input_query

    @property
    def query_changed(self) -> Signal:
        return self._query_changed

    def process_query(self, input_query: MessageInput) -> None:
        """Emit the signal that the query has changed"""
        self._input_query = input_query
        self._query_changed.emit()
