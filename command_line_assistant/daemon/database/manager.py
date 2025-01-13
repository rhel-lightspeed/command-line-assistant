"""Database module to handle SQLAlchemy connections and interactions."""

import logging
import uuid
from contextlib import contextmanager
from typing import Generator, Optional, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from command_line_assistant.config import Config
from command_line_assistant.daemon.database.models.base import BaseModel

logger = logging.getLogger(__name__)


# Type variable for ORM models
T = TypeVar("T")


class DatabaseError(Exception):
    """Base exception for database errors."""


class ConnectionError(DatabaseError):
    """Exception raised when connection fails."""


class QueryError(DatabaseError):
    """Exception raised when query fails."""


class DatabaseManager:
    """Class to handle database operations using SQLAlchemy."""

    def __init__(self, config: Config, echo: bool = False) -> None:
        """Initialize database connection.

        Args:
            database (Path): Path to the SQLite database file
            echo (bool): Enable SQL query logging if True
        """
        self._config = config
        self._engine: Engine = self._create_engine(echo)
        self._session_factory = sessionmaker(bind=self._engine)

    def _create_engine(self, echo: bool) -> Engine:
        """Create SQLAlchemy engine with proper settings.

        Args:
            echo (bool): Enable SQL query logging if True

        Returns:
            Engine: Configured SQLAlchemy engine

        Raises:
            ConnectionError: When invalid database settings are provided
        """
        try:
            connection_url = self._config.history.database.get_connection_url()

            # SQLite-specific settings
            connect_args = {}
            if self._config.history.database.type == "sqlite":
                connect_args["check_same_thread"] = False
                return create_engine(
                    connection_url,
                    echo=echo,
                    poolclass=StaticPool,
                    connect_args=connect_args,
                )

            # For other databases, use standard pooling
            return create_engine(
                connection_url,
                echo=echo,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
        except Exception as e:
            logger.error("Failed to create database engine: %s", e)
            raise ConnectionError(f"Could not create database engine: {e}") from e

    def connect(self) -> None:
        """Create database tables if they don't exist."""
        try:
            BaseModel.metadata.create_all(self._engine)
        except Exception as e:
            logger.error("Failed to create database tables: %s", e)
            raise ConnectionError(f"Could not create tables: {e}") from e

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Create a contextual database session.

        Yields:
            Session: SQLAlchemy session object

        Raises:
            QueryError: If session operations fail
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Database session error: %s", e)
            raise QueryError(f"Session error: {e}") from e
        finally:
            session.close()

    def add(self, instance: T) -> None:
        """Add an instance to the database.

        Args:
            instance (T): SQLAlchemy model instance to add

        Raises:
            QueryError: If adding fails
        """
        try:
            with self.session() as session:
                session.add(instance)
                session.flush()
        except Exception as e:
            logger.error("Failed to add instance: %s", e)
            raise QueryError(f"Failed to add instance: {e}") from e

    def query(self, model: type[T]) -> list[T]:
        """Query all instances of a model.

        Args:
            model (type[T]): SQLAlchemy model class to query

        Returns:
            list[T]: List of model instances

        Raises:
            QueryError: If query fails
        """
        try:
            with self.session() as session:
                return session.query(model).all()
        except Exception as e:
            logger.error("Failed to query instances: %s", e)
            raise QueryError(f"Failed to query instances: {e}") from e

    def get(self, model: type[T], id: uuid.UUID) -> Optional[T]:
        """Get a single instance by ID.

        Args:
            model (type[T]): SQLAlchemy model class
            id (uuid.UUID): Instance ID to get

        Returns:
            Optional[T]: Model instance if found, None otherwise

        Raises:
            QueryError: If query fails
        """
        try:
            with self.session() as session:
                return session.query(model).get(id)
        except Exception as e:
            logger.error("Failed to get instance: %s", e)
            raise QueryError(f"Failed to get instance: {e}") from e
