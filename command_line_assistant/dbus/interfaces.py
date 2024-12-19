from typing import Optional

from dasbus.server.interface import dbus_interface
from dasbus.server.property import emits_properties_changed
from dasbus.server.template import InterfaceTemplate
from dasbus.typing import Structure

from command_line_assistant.daemon.http.query import submit
from command_line_assistant.dbus.constants import HISTORY_IDENTIFIER, QUERY_IDENTIFIER
from command_line_assistant.dbus.structures import (
    HistoryEntry,
    MessageOutput,
)
from command_line_assistant.history import handle_history_read, handle_history_write

ALLOWED_SCRIPTS = [
    "bash",
    "sh",
    "shell",
    "yaml",
    "python",
]


class CodeBlock:
    start_block: Optional[tuple[int, str]] = None
    end_block: Optional[tuple[int, str]] = None


def _parse_commands(text: str) -> list[str]:
    """Parse code blocks from LLM response and return MessageOutput object."""
    message = list(filter(None, text.splitlines()))
    allowed_scripts = [f"```{script}" for script in ALLOWED_SCRIPTS]
    code_blocks = []
    code_block = CodeBlock()
    for index, line in enumerate(message):
        if line in allowed_scripts:
            code_block.start_block = (index, line)

        if line.startswith("```") and line not in allowed_scripts:
            code_block.end_block = (index, line)

        if code_block.end_block:
            code_blocks.append(code_block)
            code_block = CodeBlock()

    # Flattened version
    commands = []
    for block in code_blocks:
        commands.extend(message[block.start_block[0] + 1 : block.end_block[0]])
    return commands


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
        output = MessageOutput()
        llm_response = submit(
            self.implementation.query.message, self.implementation.config
        )
        commands = _parse_commands(llm_response)
        output.message = llm_response
        output.command = commands
        return MessageOutput.to_structure(output)

    @emits_properties_changed
    def ProcessQuery(self, query: Structure) -> None:
        """Process the given query."""
        self.implementation.process_query(MessageOutput.from_structure(query))


@dbus_interface(HISTORY_IDENTIFIER.interface_name)
class HistoryInterface(InterfaceTemplate):
    @property
    def GetHistory(self) -> Structure:
        history = HistoryEntry()
        history.entries = handle_history_read(self.implementation.config)
        return history.to_structure(history)

    def ClearHistory(self) -> None:
        handle_history_write(self.implementation.config.history.file, [], "")
