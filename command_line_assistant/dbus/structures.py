from dasbus.structure import DBusData
from dasbus.typing import List, Str


class Message(DBusData):
    """Base class for message input and output"""

    def __init__(self) -> None:
        self._message: Str = ""
        super().__init__()

    @property
    def message(self) -> Str:
        return self._message

    @message.setter
    def message(self, value: Str) -> None:
        self._message = value


class HistoryItem(DBusData):
    """Represents a single history item with query and response"""

    def __init__(self) -> None:
        self._query: Str = ""
        self._response: Str = ""
        self._timestamp: Str = ""
        super().__init__()

    @property
    def query(self) -> Str:
        return self._query

    @query.setter
    def query(self, value: Str) -> None:
        self._query = value

    @property
    def response(self) -> Str:
        return self._response

    @response.setter
    def response(self, value: Str) -> None:
        self._response = value

    @property
    def timestamp(self) -> Str:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: Str) -> None:
        self._timestamp = value


class HistoryEntry(DBusData):
    def __init__(self) -> None:
        self._entries: List[HistoryItem] = []
        super().__init__()

    @property
    def entries(self) -> List[HistoryItem]:
        return self._entries

    @entries.setter
    def entries(self, value: List[HistoryItem]) -> None:
        # This handles setting from DBus structure
        self._entries = value

    def set_from_dict(self, entry: dict) -> None:
        """Separate method to handle conversion from history dictionary"""
        item = HistoryItem()
        item.query = entry["interaction"]["query"]["text"] or ""
        item.response = entry["interaction"]["response"]["text"] or ""
        item.timestamp = entry["timestamp"] or ""
        self._entries.append(item)
