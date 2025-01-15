"""Module to control the history plugins and provide an abstract interface to execute them."""

from typing import Optional, Type

from command_line_assistant.config import Config
from command_line_assistant.daemon.session import UserSessionManager
from command_line_assistant.history.base import BaseHistoryPlugin


class HistoryManager:
    """Manages history operations by delegating to a specific history implementation.

    Example:
        >>> effective_user_id = 1000
        >>> manager = HistoryManager(config, effective_user_id, plugin=LocalHistory)
        >>> entries = manager.read()
        >>> manager.write("How do I check disk space?", "Use df -h command...")
        >>> manager.clear()
    """

    def __init__(
        self,
        config: Config,
        effective_user_id: int,
        plugin: Optional[Type[BaseHistoryPlugin]] = None,
    ) -> None:
        """Initialize the history manager.

        Args:
            config (Config): Instance of configuration class
            effective_user_id (int): The effective user id who asked for the history.
            plugin (Optional[Type[BaseHistory]], optional): Optional history implementation class
        """
        self._config = config
        self._plugin: Optional[Type[BaseHistoryPlugin]] = None
        self._instance: Optional[BaseHistoryPlugin] = None
        self._session_manager = UserSessionManager(effective_user_id)

        # Set initial plugin if provided
        if plugin:
            self.plugin = plugin

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

        Args:
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

    def read(self) -> list[dict[str, str]]:
        """Read history entries using the current plugin.

        Raises:
            RuntimeError: If no plugin is set

        Returns:
            HistoryModel: Result from the database.
        """
        if not self._instance:
            raise RuntimeError("No history plugin set. Set plugin before operations.")

        return self._instance.read(self._session_manager.user_id)

    def write(self, query: str, response: str) -> None:
        """Write a new history entry using the current plugin.

        Args:
            query (str): The user's query
            response (str): The LLM's response

        Raises:
            RuntimeError: If no plugin is set
        """
        if not self._instance:
            raise RuntimeError("No history plugin set. Set plugin before operations.")

        self._instance.write(self._session_manager.user_id, query, response)

    def clear(self) -> None:
        """Clear all history entries.

        Raises:
            RuntimeError: If no plugin is set
        """
        if not self._instance:
            raise RuntimeError("No history plugin set. Set plugin before operations.")

        self._instance.clear(self._session_manager.user_id)
