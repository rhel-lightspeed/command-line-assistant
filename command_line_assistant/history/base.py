"""Base module to track all the abstract classes for the history module."""

import logging
from abc import ABC, abstractmethod

from command_line_assistant.config import Config
from command_line_assistant.daemon.database.models.history import HistoryModel

logger = logging.getLogger(__name__)


class BaseHistoryPlugin(ABC):
    """Abstract base class for history"""

    def __init__(self, config: Config) -> None:
        """Constructor of the class.

        Arguments:
            config (Config): Instance of config.
        """
        self._config = config

    @abstractmethod
    def read(self, user_id: str) -> list[HistoryModel]:
        """Abstract method to represent a read operation

        Arguments:
            user_id (str): The user's identifier

        Returns:
            list[HistoryModel]: Should return an instance of History schema.
        """

    @abstractmethod
    def read_from_chat(self, user_id: str, from_chat: str) -> HistoryModel:
        """Abstract method to represent a read operation from a specific chat

        Arguments:
            user_id (str): The user's identifier
            from_chat (str): The chat name

        Returns:
            HistoryModel: Should return an instance of HistoryModel.
        """

    @abstractmethod
    def write(self, chat_id: str, user_id: str, query: str, response: str) -> None:
        """Abstract method to represent a write operation

        Arguments:
            chat_id (str): The chat identifier
            user_id (str): The user's identifier
            query (str): The user question
            response (str): The LLM response
        """

    @abstractmethod
    def clear(self, user_id: str) -> None:
        """Abstract method to represent a clear operation

        Arguments:
            user_id (str): The user's identifier
        """

    @abstractmethod
    def clear_from_chat(self, user_id: str, from_chat: str) -> None:
        """Abstract method to represent a clear from chat operation

        Arguments:
            user_id (str): The user's identifier
            from_chat (str): The chat name
        """
