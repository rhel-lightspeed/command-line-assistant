import uuid
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from command_line_assistant.daemon.database.manager import (
    ConnectionError,
    DatabaseManager,
    QueryError,
)
from command_line_assistant.daemon.database.models.history import (
    HistoryModel,
    InteractionModel,
)


@pytest.fixture
def database_manager(mock_config):
    """Fixture to create a database manager instance."""
    manager = DatabaseManager(mock_config)
    manager.connect()  # Create tables
    return manager


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

    mock_config.history.database.get_connection_url = failure

    with pytest.raises(ConnectionError) as exc_info:
        DatabaseManager(mock_config)

    assert "Could not create database engine" in str(exc_info.value)


def test_connect_success(database_manager):
    """Test successful database connection."""
    try:
        database_manager.connect()
    except Exception as e:
        pytest.fail(f"connect() raised {e} unexpectedly!")


def test_connect_failure(mock_config):
    """Test database connection failure."""
    manager = DatabaseManager(mock_config)

    # Mock SQLAlchemy's create_all to raise an exception
    with patch("sqlalchemy.MetaData.create_all") as mock_create_all:
        mock_create_all.side_effect = SQLAlchemyError("Failed to create tables")

        with pytest.raises(ConnectionError) as exc_info:
            manager.connect()

        assert "Could not create tables" in str(exc_info.value)


def test_session_context_manager(database_manager):
    """Test session context manager successful operation."""
    with database_manager.session() as session:
        assert session is not None
        # Verify session is active
        assert session.is_active


def test_session_context_manager_with_error(database_manager):
    """Test session context manager handles errors properly."""
    with pytest.raises(QueryError):
        with database_manager.session():
            raise SQLAlchemyError("Database error")


def test_add_success(database_manager):
    """Test successful addition of a model instance."""
    uid = uuid.uuid4()
    interaction = InteractionModel(
        id=uid,
        query_text="test query",
        response_text="test response",
        os_distribution="RHEL",
        os_version="8",
        os_arch="x86_64",
    )

    history = HistoryModel(interaction=interaction, user_id=uuid.uuid4())

    database_manager.add(history)
    result = database_manager.get(InteractionModel, uid)
    assert result


def test_add_failure(database_manager):
    """Test failure when adding a model instance."""
    invalid_model = Mock()  # This will cause SQLAlchemy to raise an error

    with pytest.raises(QueryError) as exc_info:
        database_manager.add(invalid_model)

    assert "Failed to add instance" in str(exc_info.value)


def test_query_success(database_manager):
    """Test successful query operation."""
    # First add some data
    interaction = InteractionModel(
        query_text="test query",
        response_text="test response",
        os_distribution="RHEL",
        os_version="8",
        os_arch="x86_64",
    )
    uid = uuid.uuid4()
    history = HistoryModel(id=uid, user_id=uuid.uuid4(), interaction=interaction)

    database_manager.add(history)

    # Now query it
    results = database_manager.query(HistoryModel)
    assert len(results) > 0
    assert isinstance(results[0], HistoryModel)


def test_query_failure(database_manager):
    """Test failure during query operation."""
    with patch("sqlalchemy.orm.Session.query") as mock_query:
        mock_query.side_effect = SQLAlchemyError("Query failed")

        with pytest.raises(QueryError) as exc_info:
            database_manager.query(HistoryModel)

        assert "Failed to query instances" in str(exc_info.value)


def test_get_success(database_manager):
    """Test successful get operation."""
    # First add some data
    interaction = InteractionModel(
        query_text="test query",
        response_text="test response",
        os_distribution="RHEL",
        os_version="8",
        os_arch="x86_64",
    )

    uid = uuid.uuid4()
    history = HistoryModel(
        id=uid,
        user_id=uuid.uuid4(),
        interaction=interaction,
    )
    database_manager.add(history)

    # Now get it by ID
    result = database_manager.get(HistoryModel, uid)
    assert result


def test_get_failure(database_manager):
    """Test failure during get operation."""
    with patch("sqlalchemy.orm.Session.query") as mock_query:
        mock_query.side_effect = SQLAlchemyError("Get failed")

        with pytest.raises(QueryError) as exc_info:
            database_manager.get(HistoryModel, "123")

        assert "Failed to get instance" in str(exc_info.value)
