import json
import logging

from command_line_assistant.history.base import BaseHistory
from command_line_assistant.history.schemas import History

logger = logging.getLogger(__name__)


class LocalHistory(BaseHistory):
    def read(self) -> History:
        """
        Reads the history from a file and returns it as a list of dictionaries.
        """
        history = History()
        if not self._check_if_history_is_enabled():
            return history

        filepath = self._config.history.file

        try:
            data = filepath.read_text()
            return History.from_json(data)
        except json.JSONDecodeError as e:
            logger.error("Failed to read history file %s: %s", filepath, e)
            return history

    def write(self, current_history: History, query: str, response: str) -> None:
        """
        Writes the history to a file.
        """
        if not self._check_if_history_is_enabled():
            return

        filepath = self._config.history.file
        final_history = self._add_new_entry(current_history, query, response)
        try:
            filepath.write_text(final_history.to_json())
        except json.JSONDecodeError as e:
            logger.error("Failed to write history file %s: %s", filepath, e)

    def clear(self) -> None:
        """Clear all history entries."""
        # Write empty history
        current_history = History()

        try:
            self._config.history.file.write_text(current_history.to_json())
            logger.info("History cleared successfully")
        except Exception as e:
            logger.error("Failed to clear history: %s", e)
