"""Database module to handle SQLAlchemy connections and interactions."""

import logging
import pathlib
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from command_line_assistant.config import Config
from command_line_assistant.daemon.database.models.base import BaseModel
from command_line_assistant.utils.files import create_folder

logger = logging.getLogger(__name__)


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

        Arguments:
            database (Path): Path to the SQLite database file
            echo (bool): Enable SQL query logging if True
        """
        self._config = config
        self._engine: Engine = self._create_engine(echo)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

        self._connect()

    def _create_engine(self, echo: bool) -> Engine:
        """Create SQLAlchemy engine with proper settings.

        Arguments:
            echo (bool): Enable SQL query logging if True

        Returns:
            Engine: Configured SQLAlchemy engine

        Raises:
            ConnectionError: When invalid database settings are provided
        """
        try:
            connection_url = self._config.database.get_connection_url()
            # SQLite-specific settings
            if self._config.database.type == "sqlite":
                if self._config.database.connection_string is not None:
                    create_folder(
                        pathlib.Path(self._config.database.connection_string).parent,
                        parents=True,
                    )
                return create_engine(
                    connection_url,
                    echo=echo,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
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

    def _connect(self) -> None:
        """Create database tables if they don't exist."""
        try:
            # Order here is the name of the table that will be created
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
