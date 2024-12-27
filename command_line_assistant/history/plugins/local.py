"""Plugin for handling local history managemnet."""

import json
import logging

from command_line_assistant.dbus.exceptions import (
    CorruptedHistoryError,
    MissingHistoryFileError,
)
from command_line_assistant.history.base import BaseHistory
from command_line_assistant.history.schemas import History

logger = logging.getLogger(__name__)


class LocalHistory(BaseHistory):
    """Class meant to manage the conversation history locally."""

    def read(self) -> History:
        """Reads the history from a file and returns it as a list of dictionaries.

        Raises:
            CorruptedHistoryError: Raised when the file is corrupted or the json can't be serialized.
            MissingHistoryFileError: Raised when the history file could not be found.

        Returns:
            History: An instance of a `py:History` class that holds the history data.
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
            raise CorruptedHistoryError(
                f"The history file {filepath} seems to be corrupted. Can't load the file."
            ) from e
        except FileNotFoundError as e:
            logger.error("History file does not exist %s: %s", filepath, e)
            raise MissingHistoryFileError(
                f"The history file {filepath} is missing."
            ) from e

    def write(self, current_history: History, query: str, response: str) -> None:
        """Write history to a file

        Args:
            current_history (History): An instance of the current history to append new data
            query (str): The user question
            response (str): The LLM response

        Raises:
            CorruptedHistoryError: Raised when the file is corrupted or the json can't be serialized.
            MissingHistoryFileError: Raised when the history file could not be found.
        """
        if not self._check_if_history_is_enabled():
            return

        filepath = self._config.history.file
        final_history = self._add_new_entry(current_history, query, response)
        try:
            filepath.write_text(final_history.to_json())
        except json.JSONDecodeError as e:
            logger.error("Failed to write history file %s: %s", filepath, e)
            raise CorruptedHistoryError(
                f"Can't write data to the history file {filepath}."
            ) from e
        except FileNotFoundError as e:
            logger.error("History file does not exist %s: %s", filepath, e)
            raise MissingHistoryFileError(
                f"The history file {filepath} is missing."
            ) from e

    def clear(self) -> None:
        """Clear the local history by adding a blank version of history.

        Raises:
            MissingHistoryFileError: Raised when the history file could not be found.
        """
        # Write empty history
        current_history = History()
        filepath = self._config.history.file
        try:
            filepath.write_text(current_history.to_json())
            logger.info("History cleared successfully")
        except FileNotFoundError as e:
            logger.error("History file does not exist %s: %s", filepath, e)
            raise MissingHistoryFileError(
                f"The history file {filepath} is missing."
            ) from e
