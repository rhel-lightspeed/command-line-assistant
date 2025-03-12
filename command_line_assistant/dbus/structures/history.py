"""Module to hold structures related to the history functionality."""

from typing import Optional

from dasbus.structure import DBusData
from dasbus.typing import List, Str

from command_line_assistant.dbus.structures.base import BaseDataMixin


class HistoryEntry(BaseDataMixin, DBusData):
    """Represents a single history item with query and response"""

    def __init__(
        self,
        question: Str = "",
        response: Str = "",
        chat_name: Str = "",
        created_at: Str = "",
    ) -> None:
        """Constructor of class.

        Arguments:
            question (Str): The user question
            response (Str): The llm response
            chat_name (Str): The name of the chat associated with the question
            created_at (Str): When the record was created.
        """
        self._question: Str = question
        self._response: Str = response
        self._chat_name: Str = chat_name
        self._created_at: Str = created_at
        super().__init__()

    @property
    def question(self) -> Str:
        """Property for internal question attribute.

        Returns:
            Str: The value of question
        """
        return self._question

    @question.setter
    def question(self, value: Str) -> None:
        """Set a new question

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._question = value

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

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._response = value

    @property
    def chat_name(self) -> Str:
        """Property for internal chat_name attribute.

        Returns:
            Str: The value of chat_name
        """
        return self._chat_name

    @chat_name.setter
    def chat_name(self, value: Str) -> None:
        """Set a new chat_name

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._chat_name = value

    @property
    def created_at(self) -> Str:
        """Property for internal created_at attribute.

        Returns:
            Str: The value of created_at
        """
        return self._created_at

    @created_at.setter
    def created_at(self, value: Str) -> None:
        """Set a new created_at

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._created_at = value


class HistoryList(BaseDataMixin, DBusData):
    """Represents history entries"""

    def __init__(self, histories: Optional[List[HistoryEntry]] = None) -> None:
        """Constructor of the class.

        Arguments:
            histories (Optional[List[HistoryEntry]], optional): A list of `HistoryEntry` to hold.
        """
        self._histories: List[HistoryEntry] = histories or []
        super().__init__()

    @property
    def histories(self) -> List[HistoryEntry]:
        """Property for internal entries attribute.

        Returns:
            List[HistoryEntry]: List of history items contained in the user history.
        """
        return self._histories

    @histories.setter
    def histories(self, value: List[HistoryEntry]) -> None:
        """Set new entries

        Arguments:
            value (List[HistoryItem]): List of values to be set to the internal property
        """
        # This handles setting from DBus structure
        self._histories = value
