"""D-Bus structures that defines and powers our commands."""

from dasbus.structure import DBusData
from dasbus.typing import Int, List, Str


class MessageInput(DBusData):
    """Represents the input message to be sent to the backend"""

    def __init__(self) -> None:
        """Constructor of the class."""
        self._question: Str = ""
        self._stdin: Str = ""
        self._attachment_contents: Str = ""
        self._attachment_mimetype: Str = ""

        self._user: Int = 0
        super().__init__()

    @property
    def question(self) -> Str:
        """Property for internal message attribute.

        Returns:
            Str: Value of message
        """
        return self._question

    @question.setter
    def question(self, value: Str) -> None:
        """Set a new question

        Args:
            value (Str): Question to be set to the internal property
        """
        self._question = value

    @property
    def stdin(self) -> Str:
        """Property for internal stdin attribute.

        Returns:
            Str: Value of stdin
        """
        return self._stdin

    @stdin.setter
    def stdin(self, value: Str) -> None:
        """Set a new stdin

        Args:
            value (Str): Value to be set to the internal property
        """
        self._stdin = value

    @property
    def attachment_contents(self) -> Str:
        """Property for internal attachment_contents attribute.

        Returns:
            Str: Value of attachment_contents
        """
        return self._attachment_contents

    @attachment_contents.setter
    def attachment_contents(self, value: Str) -> None:
        """Set a new attachment_contents

        Args:
            value (Str): Value to be set to the internal property
        """
        self._attachment_contents = value

    @property
    def attachment_mimetype(self) -> Str:
        """Property for internal attachment_mimetype attribute.

        Returns:
            Str: Value of attachment_mimetype
        """
        return self._attachment_mimetype

    @attachment_mimetype.setter
    def attachment_mimetype(self, value: Str) -> None:
        """Set a new attachment_mimetype

        Args:
            value (Str): Value to be set to the internal property
        """
        self._attachment_mimetype = value

    @property
    def user(self) -> Int:
        """Property for internal user attribute.

        Returns:
            Str: Value of user
        """
        return self._user

    @user.setter
    def user(self, value: Int) -> None:
        """Set a new user

        Args:
            value (Int): Value to be set to the internal property
        """
        self._user = value

    def from_dict(self, data: dict) -> None:
        """Set the internal properties from a dictionary.

        Args:
            data (dict): The dictionary to be used to set the internal properties.
        """
        self._question = data["question"]
        self._stdin = data["stdin"]
        self._attachment_contents = data["attachment_contents"]
        self._attachment_mimetype = data["attachment_mimetype"]
        self._user = data["user"]


class Message(DBusData):
    """Base class for message input and output"""

    def __init__(self) -> None:
        """Constructor of class."""
        self._message: Str = ""
        self._user: Str = ""
        super().__init__()

    @property
    def message(self) -> Str:
        """Property for internal message attribute.

        Returns:
            Str: Value of message
        """
        return self._message

    @message.setter
    def message(self, value: Str) -> None:
        """Set a new message

        Args:
            value (Str): Message to be set to the internal property
        """
        self._message = value

    @property
    def user(self) -> Str:
        """Property for internal user attribute.

        Returns:
            Str: Value of user
        """
        return self._user

    @user.setter
    def user(self, value: Str) -> None:
        """Set a new user

        Args:
            value (Str): User to be set to the internal property
        """
        self._user = value


class HistoryItem(DBusData):
    """Represents a single history item with query and response"""

    def __init__(self) -> None:
        """Constructor of class."""
        self._query: Str = ""
        self._response: Str = ""
        self._timestamp: Str = ""
        super().__init__()

    @property
    def query(self) -> Str:
        """Property for internal query attribute.

        Returns:
            Str: The value of query
        """
        return self._query

    @query.setter
    def query(self, value: Str) -> None:
        """Set a new query

        Args:
            value (Str): Value to be set to the internal property
        """
        self._query = value

    @property
    def response(self) -> Str:
        """Property for internal response attribute.

        Returns:
            Str: The value of response
        """
        return self._response

    @response.setter
    def response(self, value: Str) -> None:
        """Set a new response

        Args:
            value (Str): Value to be set to the internal property
        """
        self._response = value

    @property
    def timestamp(self) -> Str:
        """Property for internal timestamp attribute.

        Returns:
            Str: The value of timestamp
        """
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: Str) -> None:
        """Set a new timestamp

        Args:
            value (Str): Value to be set to the internal property
        """
        self._timestamp = value


class HistoryEntry(DBusData):
    """Represents history entries"""

    def __init__(self) -> None:
        """Constructor of the class."""
        self._entries: List[HistoryItem] = []
        super().__init__()

    @property
    def entries(self) -> List[HistoryItem]:
        """Property for internal entries attribute.

        Returns:
            List[HistoryItem]: List of history items contained in the user history.
        """
        return self._entries

    @entries.setter
    def entries(self, value: List[HistoryItem]) -> None:
        """Set new entries

        Args:
            value (List[HistoryItem]): List of values to be set to the internal property
        """
        # This handles setting from DBus structure
        self._entries = value

    def set_from_dict(self, entry: dict) -> None:
        """Helper method to handle conversion from history dictionary

        Args:
            entry (dict): The entry in form of a dictionary.
        """
        item = HistoryItem()
        item.query = entry["interaction"]["query"]["text"] or ""
        item.response = entry["interaction"]["response"]["text"] or ""
        item.timestamp = entry["timestamp"] or ""
        self._entries.append(item)
