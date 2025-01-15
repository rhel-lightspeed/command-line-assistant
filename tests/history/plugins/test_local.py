import uuid
from unittest.mock import Mock, create_autospec, patch

import pytest

from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.dbus.exceptions import (
    CorruptedHistoryError,
    MissingHistoryFileError,
)
from command_line_assistant.history.plugins.local import LocalHistory


@pytest.fixture
def local_history(mock_config: Mock) -> LocalHistory:
    """Fixture for LocalHistory instance with mocked dependencies."""
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
        assert local_history.read(uuid.uuid4()) == []

    def test_read_success(self, local_history: LocalHistory):
        """Should successfully read and format history entries."""
        # Create mock history entries
        uid = uuid.uuid4()
        local_history.write(uid, "test query", "test response")
        result = local_history.read(uid)

        assert len(result) == 1
        assert result[0]["query"] == "test query"
        assert result[0]["response"] == "test response"
        assert "timestamp" in result[0]

    def test_read_failure(self, local_history: LocalHistory):
        """Should raise CorruptedHistoryError on read failure."""
        with pytest.raises(CorruptedHistoryError, match="Failed to read from database"):
            local_history.read("1")  # type: ignore


class TestLocalHistoryWrite:
    """Test cases for writing history."""

    def test_write_disabled_history(
        self, local_history: LocalHistory, mock_config: Mock
    ):
        """Should not write when history is disabled."""
        mock_config.history.enabled = False
        uid = uuid.uuid4()
        local_history.write(uid, "query", "response")
        assert not local_history.read(uid)

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
        query: str,
        response: str,
    ):
        """Should successfully write history entries."""
        uid = uuid.uuid4()
        local_history.write(uid, query, response)
        assert len(local_history.read(uid)) == 1

    def test_write_failure(self, local_history: LocalHistory):
        """Should raise CorruptedHistoryError on write failure."""
        with pytest.raises(CorruptedHistoryError, match="Failed to write to database"):
            local_history.write("1", "query", "response")  # type: ignore


class TestLocalHistoryClear:
    """Test cases for clearing history."""

    def test_clear_success(self, local_history: LocalHistory):
        """Should successfully clear history."""
        uid = uuid.uuid4()
        local_history.write(uid, "test", "test")
        local_history.clear(uid)

        # Verify soft delete was performed
        assert not local_history.read(uid)

    def test_clear_failure(self, local_history: LocalHistory):
        """Should raise MissingHistoryFileError on clear failure."""
        with pytest.raises(MissingHistoryFileError, match="Failed to clear database"):
            local_history.clear("bb5b3a3e-d2a7-11ef-a682-52b437312584i9090")  # type: ignore
