import logging
from unittest.mock import Mock, patch

import pytest
from dasbus.error import DBusError

from command_line_assistant.commands.history import (
    HistoryCommand,
    _initialize_qa_renderer,
    _initialize_spinner_renderer,
    _initialize_text_renderer,
)
from command_line_assistant.dbus.structures import HistoryEntry, HistoryItem


@pytest.fixture
def mock_proxy():
    """Create a mock DBus proxy."""
    proxy = Mock()
    return proxy


@pytest.fixture
def history_command(mock_proxy):
    """Create a HistoryCommand instance with mocked proxy."""
    with patch(
        "command_line_assistant.commands.history.HISTORY_IDENTIFIER.get_proxy",
        return_value=mock_proxy,
    ):
        command = HistoryCommand(clear=False, first=False, last=False)
        return command


@pytest.fixture
def sample_history_entry():
    """Create a sample history entry for testing."""
    entry = HistoryItem()
    entry.query = "test query"
    entry.response = "test response"
    entry.timestamp = "2024-01-01T00:00:00Z"

    history_entry = HistoryEntry()
    history_entry.entries = [entry]
    return history_entry


def test_initialize_renderers():
    """Test initialization of various renderers."""
    spinner = _initialize_spinner_renderer()
    qa = _initialize_qa_renderer()
    text = _initialize_text_renderer()

    assert spinner is not None
    assert qa is not None
    assert text is not None


def test_retrieve_all_conversations_success(
    history_command, mock_proxy, sample_history_entry, caplog
):
    """Test retrieving all conversations successfully."""
    mock_proxy.GetHistory.return_value = sample_history_entry.to_structure(
        sample_history_entry
    )

    with caplog.at_level(logging.INFO):
        history_command._retrieve_all_conversations()

    assert "Getting all conversations from history" in caplog.text
    mock_proxy.GetHistory.assert_called_once()


def test_retrieve_all_conversations_empty(history_command, mock_proxy, caplog, capsys):
    """Test retrieving all conversations when history is empty."""
    empty_history = HistoryEntry()
    empty_history.entries = []
    mock_proxy.GetHistory.return_value = empty_history.to_structure(empty_history)

    history_command._retrieve_all_conversations()
    captured = capsys.readouterr()
    assert captured.out == "No history found.\n"


def test_retrieve_all_conversations_error(history_command, mock_proxy, caplog):
    """Test retrieving all conversations with DBus error."""
    mock_proxy.GetHistory.side_effect = DBusError("test.error", "Test error")

    with pytest.raises(DBusError):
        with caplog.at_level(logging.INFO):
            history_command._retrieve_all_conversations()

    assert "Failed to get history" in caplog.text


def test_retrieve_first_conversation_success(
    history_command, mock_proxy, sample_history_entry
):
    """Test retrieving first conversation successfully."""
    mock_proxy.GetFirstConversation.return_value = sample_history_entry.to_structure(
        sample_history_entry
    )

    history_command._retrieve_first_conversation()

    mock_proxy.GetFirstConversation.assert_called_once()


def test_retrieve_first_conversation_empty(history_command, mock_proxy, capsys):
    """Test retrieving first conversation when history is empty."""
    empty_history = HistoryEntry()
    empty_history.entries = []
    mock_proxy.GetFirstConversation.return_value = empty_history.to_structure(
        empty_history
    )

    history_command._retrieve_first_conversation()
    captured = capsys.readouterr()
    assert captured.out == "No history found.\n"


def test_retrieve_first_conversation_error(history_command, mock_proxy, caplog):
    """Test retrieving first conversation with DBus error."""
    mock_proxy.GetFirstConversation.side_effect = DBusError("test.error", "Test error")

    with pytest.raises(DBusError):
        with caplog.at_level(logging.INFO):
            history_command._retrieve_first_conversation()

    assert "Failed to get first conversation" in caplog.text


def test_retrieve_last_conversation_success(
    history_command, mock_proxy, sample_history_entry
):
    """Test retrieving last conversation successfully."""
    mock_proxy.GetLastConversation.return_value = sample_history_entry.to_structure(
        sample_history_entry
    )

    history_command._retrieve_last_conversation()

    mock_proxy.GetLastConversation.assert_called_once()


def test_retrieve_last_conversation_empty(history_command, mock_proxy, capsys):
    """Test retrieving last conversation when history is empty."""
    empty_history = HistoryEntry()
    empty_history.entries = []
    mock_proxy.GetLastConversation.return_value = empty_history.to_structure(
        empty_history
    )

    history_command._retrieve_last_conversation()
    captured = capsys.readouterr()
    assert captured.out == "No history found.\n"


def test_retrieve_last_conversation_error(history_command, mock_proxy, caplog):
    """Test retrieving last conversation with DBus error."""
    mock_proxy.GetLastConversation.side_effect = DBusError("test.error", "Test error")

    with pytest.raises(DBusError):
        with caplog.at_level(logging.INFO):
            history_command._retrieve_last_conversation()

    assert "Failed to get last conversation" in caplog.text


def test_clear_history_success(history_command, mock_proxy, caplog):
    """Test clearing history successfully."""
    with caplog.at_level(logging.INFO):
        history_command._clear_history()

    assert "Cleaning the history" in caplog.text
    mock_proxy.ClearHistory.assert_called_once()


def test_clear_history_error(history_command, mock_proxy, caplog):
    """Test clearing history with DBus error."""
    mock_proxy.ClearHistory.side_effect = DBusError("test.error", "Test error")

    with pytest.raises(DBusError):
        with caplog.at_level(logging.INFO):
            history_command._clear_history()

    assert "Failed to clean the history" in caplog.text


def test_run_clear(history_command):
    """Test run method with clear flag."""
    history_command._clear = True
    with patch.object(history_command, "_clear_history") as mock_clear:
        history_command.run()
        mock_clear.assert_called_once()


def test_run_first(history_command):
    """Test run method with first flag."""
    history_command._first = True
    with patch.object(history_command, "_retrieve_first_conversation") as mock_first:
        history_command.run()
        mock_first.assert_called_once()


def test_run_last(history_command):
    """Test run method with last flag."""
    history_command._last = True
    with patch.object(history_command, "_retrieve_last_conversation") as mock_last:
        history_command.run()
        mock_last.assert_called_once()


def test_run_all(history_command):
    """Test run method with no flags (all conversations)."""
    with patch.object(history_command, "_retrieve_all_conversations") as mock_all:
        history_command.run()
        mock_all.assert_called_once()
