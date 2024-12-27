"""Module to control the history plugins and provide an abstract interface to execute them."""

from typing import Optional, Type

from command_line_assistant.config import Config
from command_line_assistant.history.base import BaseHistory
from command_line_assistant.history.schemas import History


class HistoryManager:
    """Manages history operations by delegating to a specific history implementation.

    Example:
        >>> manager = HistoryManager(config, plugin=LocalHistory)
        >>> entries = manager.read()
        >>> manager.write("How do I check disk space?", "Use df -h command...")
        >>> manager.clear()
    """

    def __init__(
        self, config: Config, plugin: Optional[Type[BaseHistory]] = None
    ) -> None:
        """Initialize the history manager.

        Args:
            config (Config): Instance of configuration class
            plugin (Optional[Type[BaseHistory]], optional): Optional history implementation class
        """
        self._config = config
        self._plugin: Optional[Type[BaseHistory]] = None
        self._instance: Optional[BaseHistory] = None

        # Set initial plugin if provided
        if plugin:
            self.plugin = plugin

    @property
    def plugin(self) -> Optional[Type[BaseHistory]]:
        """Property for the internal plugin attribute

        Returns:
            Optional[Type[BaseHistory]]: Instance of the provided plugin (if any)
        """
        return self._plugin

    @plugin.setter
    def plugin(self, plugin_cls: Type[BaseHistory]) -> None:
        """Set and initialize a new plugin.

        Args:
            plugin_cls (Type[BaseHistory]): History implementation class to use

        Raises:
            TypeError: If plugin_cls is not a subclass of BaseHistory
        """
        if not issubclass(plugin_cls, BaseHistory):
            raise TypeError(
                f"Plugin must be a subclass of BaseHistory, got {plugin_cls.__name__}"
            )

        self._plugin = plugin_cls
        self._instance = plugin_cls(self._config)

    def read(self) -> History:
        """Read history entries using the current plugin.

        Raises:
            RuntimeError: If no plugin is set

        Returns:
            History object containing entries and metadata
        """
        if not self._instance:
            raise RuntimeError("No history plugin set. Set plugin before operations.")

        return self._instance.read()

    def write(self, current_history: History, query: str, response: str) -> None:
        """Write a new history entry using the current plugin.

        Args:
            current_history (History): The current user history
            query (str): The user's query
            response (str): The LLM's response

        Raises:
            RuntimeError: If no plugin is set
        """
        if not self._instance:
            raise RuntimeError("No history plugin set. Set plugin before operations.")

        self._instance.write(current_history, query, response)

    def clear(self) -> None:
        """Clear all history entries.

        Raises:
            RuntimeError: If no plugin is set
        """
        if not self._instance:
            raise RuntimeError("No history plugin set. Set plugin before operations.")

        self._instance.clear()
