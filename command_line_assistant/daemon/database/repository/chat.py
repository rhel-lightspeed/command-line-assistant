"""Module to hold the chat repository."""

from sqlalchemy import asc, select

from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.models.chat import ChatModel
from command_line_assistant.daemon.database.repository.base import BaseRepository


class ChatRepository(BaseRepository):
    """Class that implements the chat repository methods."""

    def __init__(self, manager: DatabaseManager, model: type[ChatModel] = ChatModel):
        """Default constructor for chat repository.

        Arguments:
            manager (DatabaseManager): The database manager instance.
            model (ChatModel): The SQLAlchemy model to use in the repository.
        """
        super().__init__(manager=manager, model=model)

    def select_latest_chat(self, user_id: str) -> ChatModel:
        """Select the latest chat for a given user

        Arguments:
            user_id (str): The user's identifier

        Returns:
            ChatModel: The chat entry
        """
        statement = (
            select(self._model)
            .where(self._model.user_id == user_id)
            .filter(self._model.deleted_at.is_(None))
            .order_by(asc(self._model.created_at))
        )

        with self._manager.session() as session:
            return session.execute(statement=statement).scalars().first()  # type: ignore
