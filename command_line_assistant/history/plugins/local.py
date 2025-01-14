"""Plugin for handling local history managemnet."""

import logging
import platform
import uuid
from datetime import datetime

from sqlalchemy import asc

from command_line_assistant.config import Config
from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.models.history import (
    HistoryModel,
    InteractionModel,
)
from command_line_assistant.dbus.exceptions import (
    CorruptedHistoryError,
    MissingHistoryFileError,
)
from command_line_assistant.history.base import BaseHistoryPlugin

logger = logging.getLogger(__name__)


class LocalHistory(BaseHistoryPlugin):
    """Class meant to manage the conversation history locally."""

    def __init__(self, config: Config) -> None:
        """Default constructor for class

        Args:
            config (Config): Configuration class
        """
        super().__init__(config)
        self._db: DatabaseManager = self._initialize_database()

    def _initialize_database(self) -> DatabaseManager:
        """Initialize the database connection and create tables if needed.

        Returns:
            Database: A new instance of the database.

        Raises:
            MissingHistoryFileError: If the database cannot be initialized properly.
        """
        try:
            db = DatabaseManager(self._config)
            db.connect()
            return db
        except Exception as e:
            logger.error("Failed to initialize database: %s", e)
            raise MissingHistoryFileError(f"Could not initialize database: {e}") from e

    def read(self) -> list[dict[str, str]]:
        """Reads the history from the database.

        Returns:
            History: An instance of a History class that holds the history data.

        Raises:
            CorruptedHistoryError: Raised when there's an error reading from the database.
            MissingHistoryFileError: Raised when the database file is missing.
        """
        if not self._check_if_history_is_enabled():
            return []

        try:
            with self._db.session() as session:
                # Query history entries with relationships
                entries = (
                    session.query(HistoryModel)
                    .join(InteractionModel)
                    .filter(HistoryModel.deleted_at.is_(None))
                    .order_by(asc(HistoryModel.timestamp))
                    .all()
                )

                return [
                    {
                        "query": entry.interaction.query_text,
                        "response": entry.interaction.response_text,
                        "timestamp": str(entry.timestamp),
                    }
                    for entry in entries
                ]
        except Exception as e:
            logger.error("Failed to read from database: %s", e)
            raise CorruptedHistoryError(f"Failed to read from database: {e}") from e

    def write(self, query: str, response: str) -> None:
        """Write history to the database.

        Args:
            query (str): The user question
            response (str): The LLM response

        Raises:
            CorruptedHistoryError: Raised when there's an error writing to the database.
            MissingHistoryFileError: Raised when the database file is missing.
        """
        if not self._check_if_history_is_enabled():
            return

        try:
            with self._db.session() as session:
                # Create Interaction record
                interaction = InteractionModel(
                    query_text=query,
                    response_text=response,
                    response_tokens=len(response),
                    session_id=uuid.uuid4(),
                    os_distribution="RHEL",  # Default to RHEL for now
                    os_version=platform.release(),
                    os_arch=platform.machine(),
                )
                session.add(interaction)

                # Create History record
                history = HistoryModel(
                    interaction=interaction,
                )
                session.add(history)
        except Exception as e:
            logger.error("Failed to write to database: %s", e)
            raise CorruptedHistoryError(f"Failed to write to database: {e}") from e

    def clear(self) -> None:
        """Clear the database by dropping and recreating tables.

        Raises:
            MissingHistoryFileError: Raised when the database file is missing.
        """
        try:
            with self._db.session() as session:
                # Soft delete by setting deleted_at
                session.query(HistoryModel).update(
                    {"deleted_at": datetime.utcnow()}, synchronize_session=False
                )
            logger.info("Database cleared successfully")
        except Exception as e:
            logger.error("Failed to clear database: %s", e)
            raise MissingHistoryFileError(f"Failed to clear database: {e}") from e
