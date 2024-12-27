import json
import logging
from unittest.mock import patch

import pytest

from command_line_assistant.dbus.exceptions import (
    CorruptedHistoryError,
    MissingHistoryFileError,
)
from command_line_assistant.history.plugins.local import LocalHistory
from command_line_assistant.history.schemas import (
    History,
    HistoryMetadata,
)


@pytest.fixture
def local_history(mock_config):
    """Create a LocalHistory instance for testing."""
    return LocalHistory(mock_config)


@pytest.fixture
def sample_history_data():
    """Create sample history data for testing."""
    return {
        "history": [
            {
                "id": "test-id",
                "timestamp": "2024-01-01T00:00:00Z",
                "interaction": {
                    "query": {"text": "test query", "role": "user"},
                    "response": {
                        "text": "test response",
                        "tokens": 2,
                        "role": "assistant",
                    },
                },
                "metadata": {
                    "session_id": "test-session",
                    "os_info": {
                        "distribution": "RHEL",
                        "version": "test",
                        "arch": "x86_64",
                    },
                },
            }
        ],
        "metadata": {
            "last_updated": "2024-01-01T00:00:00Z",
            "version": "0.1.0",
            "entry_count": 1,
            "size_bytes": 0,
        },
    }


def test_read_when_history_disabled(local_history):
    """Test reading history when history is disabled."""
    local_history._config.history.enabled = False

    history = local_history.read()

    assert isinstance(history, History)
    assert len(history.history) == 0
    assert isinstance(history.metadata, HistoryMetadata)


def test_read_existing_history(local_history, sample_history_data):
    """Test reading existing history file."""
    with patch("pathlib.Path.read_text") as mock_read:
        mock_read.return_value = json.dumps(sample_history_data)

        history = local_history.read()

        assert isinstance(history, History)
        assert len(history.history) == 1
        assert history.history[0].interaction.query.text == "test query"
        assert history.history[0].interaction.response.text == "test response"
        assert history.metadata.entry_count == 1


def test_read_invalid_json(local_history, caplog):
    """Test reading invalid JSON history file."""
    with patch("pathlib.Path.read_text") as mock_read:
        mock_read.return_value = "invalid json"

        with (
            caplog.at_level(logging.ERROR),
            pytest.raises(CorruptedHistoryError, match="seems to be corrupted."),
        ):
            local_history.read()


def test_write_new_entry(local_history):
    """Test writing a new history entry."""
    current_history = History()
    query = "test query"
    response = "test response"

    with patch("pathlib.Path.write_text") as mock_write:
        local_history.write(current_history, query, response)

        # Verify write was called
        mock_write.assert_called_once()

        # Verify the written content
        written_data = json.loads(mock_write.call_args[0][0])
        assert len(written_data["history"]) == 1
        assert written_data["history"][0]["interaction"]["query"]["text"] == query
        assert written_data["history"][0]["interaction"]["response"]["text"] == response


def test_write_when_history_disabled(local_history):
    """Test writing history when history is disabled."""
    local_history._config.history.enabled = False
    current_history = History()

    with patch("pathlib.Path.write_text") as mock_write:
        local_history.write(current_history, "query", "response")
        mock_write.assert_not_called()


def test_write_with_error(local_history, caplog):
    """Test writing history when an error occurs."""
    current_history = History()

    with patch("pathlib.Path.write_text") as mock_write:
        mock_write.side_effect = json.JSONDecodeError("Test error", "doc", 0)

        with (
            caplog.at_level(logging.ERROR),
            pytest.raises(
                CorruptedHistoryError, match="Can't write data to the history file"
            ),
        ):
            local_history.write(current_history, "query", "response")

        assert "Failed to write history file" in caplog.text


def test_clear_history(local_history):
    """Test clearing history."""
    with patch("pathlib.Path.write_text") as mock_write:
        local_history.clear()

        mock_write.assert_called_once()
        written_data = json.loads(mock_write.call_args[0][0])
        assert len(written_data["history"]) == 0
        assert written_data["metadata"]["entry_count"] == 0


def test_clear_history_with_error(local_history, caplog):
    """Test clearing history when an error occurs."""
    with (
        caplog.at_level(logging.ERROR),
        pytest.raises(MissingHistoryFileError, match="The history file"),
    ):
        local_history.clear()


def test_check_if_history_is_enabled(local_history):
    """Test history enabled check."""
    assert local_history._check_if_history_is_enabled() is True

    local_history._config.history.enabled = False
    assert local_history._check_if_history_is_enabled() is False


def test_add_new_entry(local_history):
    """Test adding a new entry to history."""
    current_history = History()
    query = "test query"
    response = "test response"

    updated_history = local_history._add_new_entry(current_history, query, response)

    assert len(updated_history.history) == 1
    assert updated_history.history[0].interaction.query.text == query
    assert updated_history.history[0].interaction.response.text == response
    assert updated_history.metadata.entry_count == 1
