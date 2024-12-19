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
            config: Application configuration
            plugin: Optional history implementation class. Defaults to LocalHistory
        """
        self._config = config
        self._plugin: Optional[Type[BaseHistory]] = None
        self._instance: Optional[BaseHistory] = None

        # Set initial plugin if provided
        if plugin:
            self.plugin = plugin

    @property
    def plugin(self) -> Optional[Type[BaseHistory]]:
        """Get the current plugin class."""
        return self._plugin

    @plugin.setter
    def plugin(self, plugin_cls: Type[BaseHistory]) -> None:
        """Set and initialize a new plugin.

        Args:
            plugin_cls: History implementation class to use

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

        Returns:
            History object containing entries and metadata

        Raises:
            RuntimeError: If no plugin is set
        """
        if not self._instance:
            raise RuntimeError("No history plugin set. Set plugin before operations.")

        return self._instance.read()

    def write(self, current_history: History, query: str, response: str) -> None:
        """Write a new history entry using the current plugin.

        Args:
            query: The user's query
            response: The LLM's response

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
