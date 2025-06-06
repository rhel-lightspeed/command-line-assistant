"""Module to control the history plugins and provide an abstract interface to execute them."""

import logging
from typing import Optional, Type

from command_line_assistant.config import Config
from command_line_assistant.daemon.database.models.history import HistoryModel
from command_line_assistant.history.base import BaseHistoryPlugin

#: Default history plugin error message.
HISTORY_PLUGIN_ERROR_MESSAGE = "No history plugin set. Set plugin before operations."

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages history operations by delegating to a specific history implementation.

    Example:
        >>> user_id = "a658710c-de6d-11ef-ae5b-52b437312584"
        >>> chat_id = "af83c6d2-de6d-11ef-ac4d-52b437312584"
        >>> manager = HistoryManager(config, plugin=LocalHistory)
        >>> entries = manager.read(user_id)
        >>> manager.write(chat_id, user_id, "How do I check disk space?", "Use df -h command...")
        >>> manager.clear()
    """

    def __init__(
        self,
        config: Config,
        plugin: Optional[Type[BaseHistoryPlugin]] = None,
    ) -> None:
        """Initialize the history manager.

        Arguments:
            config (Config): Instance of configuration class
            user_id (int): The effective user id who asked for the history.
            plugin (Optional[Type[BaseHistory]], optional): Optional history implementation class
        """
        self._config = config
        self._plugin: Optional[Type[BaseHistoryPlugin]] = None
        self._instance: Optional[BaseHistoryPlugin] = None

        # Set initial plugin if provided
        if plugin:
            self.plugin = plugin

    @property
    def is_history_enabled(self) -> bool:
        """Check if the history is enabled in the configuration file.

        Returns:
            bool: Wether or not the history is enabled.
        """
        return self._config.history.enabled

    @property
    def plugin(self) -> Optional[Type[BaseHistoryPlugin]]:
        """Property for the internal plugin attribute

        Returns:
            Optional[Type[BaseHistory]]: Instance of the provided plugin (if any)
        """
        return self._plugin

    @plugin.setter
    def plugin(self, plugin_cls: Type[BaseHistoryPlugin]) -> None:
        """Set and initialize a new plugin.

        Arguments:
            plugin_cls (Type[BaseHistory]): History implementation class to use

        Raises:
            TypeError: If plugin_cls is not a subclass of BaseHistory
        """
        if not issubclass(plugin_cls, BaseHistoryPlugin):
            raise TypeError(
                f"Plugin must be a subclass of BaseHistory, got {plugin_cls.__name__}"
            )

        self._plugin = plugin_cls
        self._instance = plugin_cls(self._config)

    def read(self, user_id: str) -> list[HistoryModel]:
        """Read history entries using the current plugin.

        Arguments:
            user_id (str): The user's identifier

        Raises:
            RuntimeError: If no plugin is set

        Returns:
            Union[list, Sequence[Any]]: List of history entries
        """
        if not self._instance:
            raise RuntimeError(HISTORY_PLUGIN_ERROR_MESSAGE)

        return self._instance.read(user_id)

    def read_from_chat(self, user_id: str, from_chat: str) -> Optional[HistoryModel]:
        """Read history entries using the current plugin.

        Arguments:
            user_id (str): The user's identifier

        Raises:
            RuntimeError: If no plugin is set

        Returns:
            Optional[HistoryModel]: An optional single history entry
        """
        if not self._instance:
            raise RuntimeError(HISTORY_PLUGIN_ERROR_MESSAGE)

        return self._instance.read_from_chat(user_id, from_chat)

    def write(self, chat_id: str, user_id: str, query: str, response: str) -> None:
        """Write a new history entry using the current plugin.

        Arguments:
            chat_id (str): The chat's identifier
            user_id (str): The user's identifier
            query (str): The user's query
            response (str): The LLM's response

        Raises:
            RuntimeError: If no plugin is set
        """
        if not self._instance:
            raise RuntimeError(HISTORY_PLUGIN_ERROR_MESSAGE)

        self._instance.write(chat_id, user_id, query, response)

    def clear(self, user_id: str) -> None:
        """Clear all history entries.

        Arguments:
            user_id (str): The user's identifier

        Raises:
            RuntimeError: If no plugin is set
        """
        if not self._instance:
            raise RuntimeError(HISTORY_PLUGIN_ERROR_MESSAGE)

        self._instance.clear(user_id)

    def clear_from_chat(self, user_id: str, from_chat: str) -> None:
        """Clear all history entries.

        Arguments:
            user_id (str): The user's identifier

        Raises:
            RuntimeError: If no plugin is set
        """
        if not self._instance:
            raise RuntimeError(HISTORY_PLUGIN_ERROR_MESSAGE)

        self._instance.clear_from_chat(user_id, from_chat)
