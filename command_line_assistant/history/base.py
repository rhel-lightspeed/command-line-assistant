"""Base module to track all the abstract classes for the history module."""

import logging
from abc import ABC, abstractmethod

from command_line_assistant.config import Config

logger = logging.getLogger(__name__)


class BaseHistoryPlugin(ABC):
    """Abstract base class for history"""

    def __init__(self, config: Config) -> None:
        """Constructor of the class.

        Args:
            config (Config): Instance of config.
        """
        self._config = config

    @abstractmethod
    def read(self) -> list[dict[str, str]]:
        """Abstract method to represent a read operation

        Returns:
            History: Should return an instance of History schema.
        """

    @abstractmethod
    def write(self, query: str, response: str) -> None:
        """Abstract method to represent a write operation

        Args:
            query (str): The user question
            response (str): The LLM response
        """

    @abstractmethod
    def clear(self) -> None:
        """Abstract method to represent a clear operation"""

    def _check_if_history_is_enabled(self) -> bool:
        """Check if the history is enabled in the configuration file.

        Returns:
            bool: If the history is enable or not.
        """
        if not self._config.history.enabled:
            logger.info("History disabled. Nothing to do.")

        return self._config.history.enabled
