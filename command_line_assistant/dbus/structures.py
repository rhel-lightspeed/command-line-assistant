from dasbus.structure import DBusData
from dasbus.typing import Str


class BaseMessage(DBusData):
    def __init__(self) -> None:
        self._message: Str = ""
        super().__init__()

    @property
    def message(self) -> Str:
        return self._message

    @message.setter
    def message(self, value: Str) -> None:
        self._message = value


class MessageInput(BaseMessage):
    """Base class for message input"""


class MessageOutput(BaseMessage):
    """Base class for message output"""

    def __init__(self) -> None:
        self._command: list[str] = []
        super().__init__()

    @property
    def command(self) -> list[str]:
        return self._command

    @command.setter
    def command(self, value: list[str]) -> None:
        self._command = value


class HistoryEntry(DBusData):
    def __init__(self) -> None:
        self._entries: list[str] = []
        super().__init__()

    @property
    def entries(self) -> list[str]:
        return self._entries

    @entries.setter
    def entries(self, value: list[str]) -> None:
        self._entries = value
