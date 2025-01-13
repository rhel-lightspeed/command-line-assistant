import uuid
from datetime import datetime
from unittest.mock import Mock, create_autospec, patch

import pytest
from sqlalchemy.orm import Session

from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.models.history import (
    HistoryModel,
    InteractionModel,
)
from command_line_assistant.dbus.exceptions import (
    CorruptedHistoryError,
    MissingHistoryFileError,
)
from command_line_assistant.history.plugins.local import LocalHistory


@pytest.fixture
def mock_db_session() -> Mock:
    """Fixture for database session."""
    return create_autospec(Session, instance=True)


@pytest.fixture
def mock_db_manager(mock_db_session: Mock) -> Mock:
    """Fixture for DatabaseManager with mocked session."""
    db_manager = create_autospec(DatabaseManager, instance=True)
    db_manager.session.return_value.__enter__.return_value = mock_db_session
    db_manager.session.return_value.__exit__.return_value = None
    return db_manager


@pytest.fixture
def local_history(mock_config: Mock, mock_db_manager: Mock) -> LocalHistory:
    """Fixture for LocalHistory instance with mocked dependencies."""
    with patch(
        "command_line_assistant.history.plugins.local.DatabaseManager",
        return_value=mock_db_manager,
    ):
        history = LocalHistory(mock_config)
        return history


class TestLocalHistoryInitialization:
    """Test cases for LocalHistory initialization."""

    def test_initialization_success(self, mock_config: Mock):
        """Should initialize successfully."""
        with patch(
            "command_line_assistant.history.plugins.local.DatabaseManager"
        ) as mock_db:
            mock_db.return_value = create_autospec(DatabaseManager, instance=True)
            history = LocalHistory(mock_config)
            assert isinstance(history._db, DatabaseManager)

    def test_initialization_failure(self, mock_config: Mock):
        """Should raise MissingHistoryFileError on initialization failure."""
        with patch(
            "command_line_assistant.history.plugins.local.DatabaseManager"
        ) as mock_db:
            mock_db.side_effect = Exception("DB Init Error")
            with pytest.raises(
                MissingHistoryFileError, match="Could not initialize database"
            ):
                LocalHistory(mock_config)


class TestLocalHistoryRead:
    """Test cases for reading history."""

    def test_read_disabled_history(
        self, local_history: LocalHistory, mock_config: Mock
    ):
        """Should return empty list when history is disabled."""
        mock_config.history.enabled = False
        assert local_history.read() == []

    def test_read_success(self, local_history: LocalHistory, mock_db_session: Mock):
        """Should successfully read and format history entries."""
        # Create mock history entries
        mock_interaction = Mock(spec=InteractionModel)
        mock_interaction.query_text = "test query"
        mock_interaction.response_text = "test response"

        mock_history = Mock(spec=HistoryModel)
        mock_history.interaction = mock_interaction
        mock_history.timestamp = datetime.utcnow()

        mock_db_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_history
        ]

        result = local_history.read()

        assert len(result) == 1
        assert result[0]["query"] == "test query"
        assert result[0]["response"] == "test response"
        assert "timestamp" in result[0]

    def test_read_failure(self, local_history: LocalHistory, mock_db_session: Mock):
        """Should raise CorruptedHistoryError on read failure."""
        mock_db_session.query.side_effect = Exception("DB Read Error")

        with pytest.raises(CorruptedHistoryError, match="Failed to read from database"):
            local_history.read()


class TestLocalHistoryWrite:
    """Test cases for writing history."""

    def test_write_disabled_history(
        self, local_history: LocalHistory, mock_config: Mock
    ):
        """Should not write when history is disabled."""
        mock_config.history.enabled = False
        local_history.write("query", "response")
        assert local_history._db.session.call_count == 0  # type: ignore

    @pytest.mark.parametrize(
        "query,response",
        [
            ("test query", "test response"),
            ("", "empty query test"),
            ("empty response test", ""),
        ],
    )
    def test_write_success(
        self,
        local_history: LocalHistory,
        mock_db_session: Mock,
        query: str,
        response: str,
    ):
        """Should successfully write history entries."""
        with patch(
            "uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")
        ):
            local_history.write(query, response)

            # Verify interaction was created with correct attributes
            mock_db_session.add.assert_called()
            calls = mock_db_session.add.call_args_list

            # First call should be InteractionModel
            interaction = calls[0][0][0]
            assert isinstance(interaction, InteractionModel)
            assert interaction.query_text == query  # type: ignore
            assert interaction.response_text == response  # type: ignore
            assert interaction.session_id is not None

            # Second call should be HistoryModel
            history = calls[1][0][0]
            assert isinstance(history, HistoryModel)
            assert history.interaction == interaction

    def test_write_failure(self, local_history: LocalHistory, mock_db_session: Mock):
        """Should raise CorruptedHistoryError on write failure."""
        mock_db_session.add.side_effect = Exception("DB Write Error")

        with pytest.raises(CorruptedHistoryError, match="Failed to write to database"):
            local_history.write("query", "response")


class TestLocalHistoryClear:
    """Test cases for clearing history."""

    def test_clear_success(self, local_history: LocalHistory, mock_db_session: Mock):
        """Should successfully clear history."""
        local_history.clear()

        # Verify soft delete was performed
        mock_db_session.query.return_value.update.assert_called_once()
        update_args = mock_db_session.query.return_value.update.call_args[0][0]
        assert "deleted_at" in update_args
        assert isinstance(update_args["deleted_at"], datetime)

    def test_clear_failure(self, local_history: LocalHistory, mock_db_session: Mock):
        """Should raise MissingHistoryFileError on clear failure."""
        mock_db_session.query.return_value.update.side_effect = Exception(
            "DB Clear Error"
        )

        with pytest.raises(MissingHistoryFileError, match="Failed to clear database"):
            local_history.clear()


def test_integration_workflow(local_history: LocalHistory, mock_db_session: Mock):
    """Integration test for full local history workflow."""
    # Setup mock responses
    mock_db_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = []

    # Test read (empty)
    assert local_history.read() == []

    # Test write
    local_history.write("test query", "test response")
    assert (
        mock_db_session.add.call_count == 2
    )  # One for InteractionModel, one for HistoryModel

    # Test clear
    local_history.clear()
    mock_db_session.query.return_value.update.assert_called_once()
