"""Base module to track all the abstract classes for the history module."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime

from command_line_assistant.config import Config
from command_line_assistant.history.schemas import (
    History,
    HistoryEntry,
    InteractionData,
    QueryData,
    ResponseData,
)

logger = logging.getLogger(__name__)


class BaseHistory(ABC):
    """Abstract base class for history"""

    def __init__(self, config: Config) -> None:
        """Constructor of the class.

        Args:
            config (Config): Instance of config.
        """
        self._config = config

    @abstractmethod
    def read(self) -> History:
        """Abstract method to represent a read operation

        Returns:
            History: Should return an instance of History schema.
        """

    @abstractmethod
    def write(self, current_history: History, query: str, response: str) -> None:
        """Abstract method to represent a write operation

        Args:
            current_history (History): An instance of the current history to append new data
            query (str): The user question
            response (str): The LLM response
        """

    @abstractmethod
    def clear(self) -> None:
        """Abstract method to represent a clear operation"""

    def _add_new_entry(
        self, current_history: History, query: str, response: str
    ) -> History:
        """Internal method to add a new entry to the current user history

        Args:
            current_history (History): An instance of the current history to append new data
            query (str): The user question
            response (str): The LLM response

        Returns:
            History: The modified history with the new entry
        """
        new_entry = HistoryEntry(
            interaction=InteractionData(
                query=QueryData(text=query),
                response=ResponseData(
                    text=response,
                    tokens=len(
                        response.split()  # TODO(r0x0d): Simple token count, replace with actual
                    ),
                ),
            )
        )

        current_history.history.append(new_entry)
        current_history.metadata.entry_count = len(current_history.history)
        # NOTE(r0x0d): This way of getting the timestamp is deprecated in newer
        # Python versions, however, the correct method is not available in Python 3.9.
        # This would be the replacement datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        current_history.metadata.last_updated = datetime.utcnow().isoformat() + "Z"
        return current_history

    def _check_if_history_is_enabled(self) -> bool:
        """Check if the history is enabled in the configuration file.

        Returns:
            bool: If the history is enable or not.
        """
        if not self._config.history.enabled:
            logger.info("History disabled. Nothing to do.")

        return self._config.history.enabled
