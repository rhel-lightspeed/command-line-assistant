"""Module to hold the history repository"""

from datetime import datetime
from typing import Union
from uuid import UUID

from sqlalchemy import asc, select, update

from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.models.history import (
    HistoryModel,
    InteractionModel,
)
from command_line_assistant.daemon.database.repository.base import BaseRepository


class HistoryRepository(BaseRepository):
    """Class that implements the history repository methods."""

    def __init__(self, manager: DatabaseManager, model: HistoryModel = HistoryModel):
        """Default constructor for history repository.

        Arguments:
            manager (DatabaseManager): The database manager instance.
            model (HistoryModel): The SQLAlchemy model to use in the repository.
        """
        super().__init__(manager=manager, model=model)

    def select_by_chat_id(self, chat_id: Union[UUID, str]) -> HistoryModel:
        """Select a history entry by chat id.

        Arguments:
            chat_id (Union[UUID, str]): The chat's identifier

        Returns:
            HistoryModel: The history entry
        """
        statement = (
            select(self._model)
            .filter(HistoryModel.deleted_at.is_(None))
            .where(self._model.chat_id == chat_id)
        )

        with self._manager.session() as session:
            return session.execute(statement=statement).scalars().first()  # type: ignore

    def select_all_history(self, user_id: Union[UUID, str]) -> list[HistoryModel]:
        """Select all history entries by user id.

        Arguments:
            user_id (Union[UUID, str]): The user's identifier

        Returns:
            list[HistoryModel]: The history entries
        """
        statement = (
            select(self._model)
            .filter(HistoryModel.deleted_at.is_(None))
            .order_by(asc(self._model.created_at))
            .where(self._model.user_id == user_id)
        )

        with self._manager.session() as session:
            return session.execute(statement=statement).scalars().all()  # type: ignore

    def delete_all(self, user_id: Union[UUID, str]) -> None:
        """Method to remove all history from the database.

        Note:
            This method will actually call `update` internally to update the
            `deleted_at` field in the table.

        Arguments:
            user_id (Union[UUID, str]): The unique identifier to query in the database.
        """
        statement = (
            update(self._model)
            .values({"deleted_at": datetime.now()})
            .where(self._model.user_id == user_id)
        )

        with self._manager.session() as session:
            session.execute(statement=statement)


class InteractionRepository(BaseRepository):
    """Class that implements the interaction repository methods."""

    def __init__(
        self, manager: DatabaseManager, model: InteractionModel = InteractionModel
    ):
        """Default constructor for interaction repository.

        Arguments:
            manager (DatabaseManager): The database manager instance.
            model (InteractionModel): The SQLAlchemy model to use in the repository.
        """
        super().__init__(manager=manager, model=model)
