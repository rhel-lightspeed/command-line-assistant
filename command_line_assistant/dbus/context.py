from typing import Optional

from dasbus.signal import Signal

from command_line_assistant.config import Config
from command_line_assistant.dbus.structures import Message


class BaseContext:
    def __init__(self, config: Config) -> None:
        self._config = config

    @property
    def config(self) -> Config:
        """Return the configuration from this context."""
        return self._config


class QueryContext(BaseContext):
    """This is the process context that will handle anything query related"""

    def __init__(self, config: Config) -> None:
        self._input_query: Optional[Message] = None
        self._query_changed = Signal()
        super().__init__(config)

    @property
    def query(self) -> Optional[Message]:
        """Make it accessible publicly"""
        return self._input_query

    @property
    def query_changed(self) -> Signal:
        return self._query_changed

    def process_query(self, input_query: Message) -> None:
        """Emit the signal that the query has changed"""
        self._input_query = input_query
        self._query_changed.emit()


class HistoryContext(BaseContext):
    """This is the process context that will handle anything query related"""

    def __init__(self, config: Config) -> None:
        super().__init__(config)
