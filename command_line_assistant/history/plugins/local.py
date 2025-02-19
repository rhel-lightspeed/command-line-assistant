"""Plugin for handling local history managemnet."""

import logging

from command_line_assistant.config import Config
from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.models.history import HistoryModel
from command_line_assistant.daemon.database.repository.chat import ChatRepository
from command_line_assistant.daemon.database.repository.history import (
    HistoryRepository,
    InteractionRepository,
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

        Arguments:
            config (Config): Configuration class
        """
        super().__init__(config)
        manager = self._initialize_database()

        self._chat_repository = ChatRepository(manager=manager)
        self._history_repository = HistoryRepository(manager=manager)
        self._interaction_repository = InteractionRepository(manager=manager)

    def _initialize_database(self) -> DatabaseManager:
        """Initialize the database connection and create tables if needed.

        Returns:
            Database: A new instance of the database.

        Raises:
            MissingHistoryFileError: If the database cannot be initialized properly.
        """
        try:
            db = DatabaseManager(self._config)
            return db
        except Exception as e:
            logger.error("Failed to initialize database: %s", e)
            raise MissingHistoryFileError(f"Could not initialize database: {e}") from e

    def read(self, user_id: str) -> list[HistoryModel]:
        """Reads the history from the database.

        Arguments:
            user_id (str): The user's identifier

        Returns:
            list[HistoryModel]: The history entries

        Raises:
            CorruptedHistoryError: Raised when there's an error reading from the database.
            MissingHistoryFileError: Raised when the database file is missing.
        """
        try:
            return self._history_repository.select_all_history(user_id)
        except Exception as e:
            logger.error("Failed to read from database: %s", e)
            raise CorruptedHistoryError(f"Failed to read from database: {e}") from e

    def write(self, chat_id: str, user_id: str, query: str, response: str) -> None:
        """Write history to the database.

        Arguments:
            chat_id (str): The chat id
            user_id (str): The user id
            query (str): The user question
            response (str): The LLM response

        Raises:
            CorruptedHistoryError: Raised when there's an error writing to the database.
            MissingHistoryFileError: Raised when the database file is missing.
        """
        try:
            # Verify if the given chat_id has a history associated with it
            result = self._history_repository.select_by_chat_id(chat_id)

            history_id = None
            if result:
                history_id = result.id
                logger.info("Found history '%s' for user '%s'", history_id, user_id)
            else:
                history_id = self._history_repository.insert(
                    {"chat_id": chat_id, "user_id": user_id}
                )[0]
                logger.info(
                    "Wrote a new history '%s' for user '%s'", history_id, user_id
                )

            # Create Interaction record
            interaction_id = self._interaction_repository.insert(
                {
                    "question": query,
                    "response": response,
                    "history_id": history_id,
                }
            )
            logger.info("Wrote a new interaction for user '%s'.", user_id)
            logger.info(
                "New interaction '%s' for user '%s' in history '%s' that belongs to chat '%s'",
                extra={
                    "audit": True,
                    "interaction_id": interaction_id,
                    "user_id": user_id,
                    "history_id": history_id,
                    "chat_id": chat_id,
                },
            )
        except Exception as e:
            logger.error("Failed to write to database: %s", e)
            raise CorruptedHistoryError(f"Failed to write to database: {e}") from e

    def clear(self, user_id: str) -> None:
        """Clear the database by dropping and recreating tables.

        Arguments:
            user_id (str): The user's identifier

        Raises:
            MissingHistoryFileError: Raised when the database file is missing.
        """
        try:
            self._history_repository.delete_all(user_id)
            logger.info("Database cleared successfully")
        except Exception as e:
            logger.error("Failed to clear database: %s", e)
            raise MissingHistoryFileError(f"Failed to clear database: {e}") from e
