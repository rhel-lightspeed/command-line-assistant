"""Module that represents the Base repository."""

from datetime import datetime
from typing import Any, Union
from uuid import UUID

from sqlalchemy import asc, insert, select, update
from sqlalchemy.engine.row import Row

from command_line_assistant.daemon.database.manager import DatabaseManager


class BaseRepository:
    """Class that implements the base repository methods."""

    def __init__(self, manager: DatabaseManager, model: Any) -> None:
        """Default constructor for base repository.

        Arguments:
            manager (DatabaseManager): The database manager instance.
            model (Any): The SQLAlchemy model to use in the repository.
        """
        self._manager = manager
        self._model = model

    def insert(self, values: Union[list[dict[str, Any]], dict[str, Any], Any]) -> Row:
        """Default method to make insertions in the database.

        Arguments:
            values (Union[list[dict[str, Any]],dict[str, Any]]): The values to insert in the database

        Returns:
            Row: A row represented as a tuple with the id inserted.
        """
        statement = insert(self._model).values(values)

        with self._manager.session() as session:
            result = session.execute(statement=statement)
            return result.inserted_primary_key  # type: ignore

    def select(self) -> Any:
        """Default method to retrieve information from the database.

        Returns:
            Any: Information retrieved from the database
        """
        statement = select(self._model).where(
            self._model.deleted_at == None,  # noqa
        )

        with self._manager.session() as session:
            return session.execute(statement=statement).scalars().all()

    def select_all_by_id(self, identifier: Union[UUID, str]) -> Any:
        """Default method to select all entries by filtering using an identifier.

        Arguments:
            identifier (Union[UUID, str]): The unique identifier to query in the database.

        Returns:
            Any: Information retrieved from the database.
        """
        statement = (
            select(self._model)
            .where(
                self._model.id == identifier,
            )
            .filter(self._model.deleted_at.is_(None))
            .order_by(asc(self._model.created_at))
            .limit(10)
        )

        with self._manager.session() as session:
            return session.execute(statement=statement).scalars().all()

    def select_all_by_user_id(self, user_id: Union[UUID, str]) -> Any:
        """Default method to select all entries by filtering using an identifier.

        Arguments:
            user_id (Union[UUID, str]): The unique identifier to query in the database.

        Returns:
            Any: Information retrieved from the database.
        """
        statement = (
            select(self._model)
            .where(
                self._model.user_id == user_id,
            )
            .filter(self._model.deleted_at.is_(None))
            .order_by(asc(self._model.created_at))
            .limit(10)
        )

        with self._manager.session() as session:
            return session.execute(statement=statement).scalars().all()

    def select_first(self) -> Any:
        """Default method to get first information from the database.

        Returns:
            Any: The first information retrieved from the database
        """
        statement = select(self._model).where(
            self._model.deleted_at == None,  # noqa
        )

        with self._manager.session() as session:
            return session.execute(statement=statement).first()

    def select_by_id(self, identifier: Union[UUID, str]) -> Any:
        """Default method to select by filtering using an identifier.

        Arguments:
            identifier (Union[UUID, str]): The unique identifier to query in the database.

        Returns:
            Any: The information retrieved from the database.
        """
        statement = (
            select(self._model)
            .where(
                self._model.id == identifier,  # noqa
            )
            .filter(self._model.deleted_at.is_(None))
        )
        with self._manager.session() as session:
            return session.execute(statement=statement).first()

    def select_by_name(self, user_id: str, name: str) -> Any:
        """Default method to select rows by using a name.

        Arguments:
            user_id (str): The user's identifier.
            name (str): The name to query in the database.

        Returns:
            Any: The information retrieved from the database.
        """
        statement = (
            select(self._model)
            .where(
                self._model.name == name and self._model.user_id == user_id,  # noqa
            )
            .filter(self._model.deleted_at.is_(None))
        )

        with self._manager.session() as session:
            return session.execute(statement=statement).first()

    def update(self, values: dict[str, Any], identifier: Union[UUID, str]) -> None:
        """Default method to update values in the database.

        Arguments:
            values (dict[str, Any]): The values to update in the database.
            identifier (Union[UUID, str]): The unique identifier to query in the database.
        """
        statement = (
            update(self._model)
            .values(values)
            .where(
                self._model.id == identifier,
            )
        )

        with self._manager.session() as session:
            session.execute(statement=statement)

    def delete(self, identifier: Union[UUID, str]) -> None:
        """Default method to remove entries from the database.

        Note:
            This method will actually call `update` internally to update the
            `deleted_at` field in the table.

        Arguments:
            identifier (Union[UUID, str]): The unique identifier to query in the database.
        """
        statement = (
            update(self._model)
            .values({"deleted_at": datetime.now()})
            .where(self._model.id == identifier)
        )

        with self._manager.session() as session:
            session.execute(statement=statement)
