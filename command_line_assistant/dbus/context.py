"""D-Bus context classes for managing the commands"""

from typing import Optional

from dasbus.signal import Signal

from command_line_assistant.config import Config
from command_line_assistant.dbus.structures import Message


class BaseContext:
    """Base class for context that defines the structure of it."""

    def __init__(self, config: Config) -> None:
        """Constructor of the class.

        Args:
            config (Config): Instance of the configuration class.
        """
        self._config = config

    @property
    def config(self) -> Config:
        """Property for the internal config attribute.

        Returns:
            Config: Instance of the configuration class
        """
        return self._config


class QueryContext(BaseContext):
    """This is the process context that will handle anything query related"""

    def __init__(self, config: Config) -> None:
        """Constructor of the class.

        Args:
            config (Config): Instance of the configuration class
        """
        self._input_query: Optional[Message] = None
        self._query_changed = Signal()
        super().__init__(config)

    @property
    def query(self) -> Optional[Message]:
        """Property for the internal query attribute.

        Returns:
            Optional[Message]: The user query wrapped in a `py:Message` dbus structure.
        """
        return self._input_query

    def process_query(self, input_query: Message) -> None:
        """Emit the signal that the query has changed.

        Args:
            input_query (Message): The user query
        """
        self._input_query = input_query
        self._query_changed.emit()


class HistoryContext(BaseContext):
    """This is the process context that will handle anything query related"""

    def __init__(self, config: Config) -> None:
        """Constructor of the class.

        Args:
            config (Config): Instance of the configuration class.
        """
        super().__init__(config)
