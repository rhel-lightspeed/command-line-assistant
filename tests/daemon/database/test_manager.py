from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from command_line_assistant.daemon.database.manager import (
    ConnectionError,
    DatabaseManager,
    QueryError,
)


def test_database_manager_initialization(mock_config):
    """Test successful database manager initialization."""
    manager = DatabaseManager(mock_config)
    assert manager._config == mock_config
    assert manager._engine is not None
    assert manager._session_factory is not None


def test_database_manager_initialization_failure(mock_config):
    """Test database manager initialization failure."""

    def failure():
        raise Exception("Connection failed")

    mock_config.database.get_connection_url = failure

    with pytest.raises(ConnectionError) as exc_info:
        DatabaseManager(mock_config)

    assert "Could not create database engine" in str(exc_info.value)


def test_connect_success(mock_config):
    """Test successful database connection."""
    try:
        DatabaseManager(mock_config)._connect()
    except Exception as e:
        pytest.fail(f"connect() raised {e} unexpectedly!")


def test_connect_failure(mock_config):
    """Test database connection failure."""
    # Mock SQLAlchemy's create_all to raise an exception
    with patch("sqlalchemy.MetaData.create_all") as mock_create_all:
        mock_create_all.side_effect = SQLAlchemyError("Failed to create tables")

        with pytest.raises(ConnectionError) as exc_info:
            DatabaseManager(mock_config)._connect()

        assert "Could not create tables" in str(exc_info.value)


def test_session_context_manager(mock_config):
    """Test session context manager successful operation."""
    manager = DatabaseManager(mock_config)
    with manager.session() as session:
        assert session is not None
        # Verify session is active
        assert session.is_active


def test_session_context_manager_with_error(mock_config):
    """Test session context manager handles errors properly."""
    manager = DatabaseManager(mock_config)
    with pytest.raises(QueryError):
        with manager.session():
            raise SQLAlchemyError("Database error")


def test_session_raises_query_error(mock_config):
    """Test session context manager raises QueryError on exception"""
    manager = DatabaseManager(mock_config)

    with pytest.raises(QueryError):
        with manager.session():
            # Force an error within the session
            raise Exception("Test exception")
