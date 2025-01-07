from unittest.mock import patch

import pytest

from command_line_assistant.commands.history import (
    HistoryCommand,
)
from command_line_assistant.dbus.structures import HistoryEntry, HistoryItem


# Mock the entire DBus service/constants module
@pytest.fixture(autouse=True)
def mock_dbus_service(mock_proxy):
    """Fixture to mock DBus service and automatically use it for all tests"""
    with patch(
        "command_line_assistant.commands.history.HISTORY_IDENTIFIER"
    ) as mock_service:
        # Create a mock proxy that will be returned by get_proxy()
        mock_service.get_proxy.return_value = mock_proxy

        yield mock_proxy


@pytest.fixture
def sample_history_entry():
    """Create a sample history entry for testing."""
    entry = HistoryItem()
    entry.query = "test query"
    entry.response = "test response"
    entry.timestamp = "2024-01-01T00:00:00Z"

    last = HistoryItem()
    last.query = "test final query"
    last.response = "test final response"
    last.timestamp = "2024-01-02T00:00:00Z"

    history_entry = HistoryEntry()
    history_entry.entries = [entry, last]
    return history_entry


def test_retrieve_all_conversations_success(mock_proxy, sample_history_entry, capsys):
    """Test retrieving all conversations successfully."""
    mock_proxy.GetHistory.return_value = sample_history_entry.to_structure(
        sample_history_entry
    )

    HistoryCommand(clear=False, first=False, last=False)._retrieve_all_conversations()

    captured = capsys.readouterr()
    assert "Getting all conversations from history" in captured.out
    mock_proxy.GetHistory.assert_called_once()


def test_retrieve_all_conversations_empty(mock_proxy, capsys):
    """Test retrieving all conversations when history is empty."""
    empty_history = HistoryEntry()
    mock_proxy.GetHistory.return_value = empty_history.to_structure(empty_history)

    HistoryCommand(clear=False, first=False, last=False)._retrieve_all_conversations()
    captured = capsys.readouterr()
    assert "No history found.\n" in captured.out


def test_retrieve_conversation_filtered_empty(mock_proxy, capsys):
    """Test retrieving first conversation when history is empty."""
    empty_history = HistoryEntry()
    mock_proxy.GetFilteredConversation.return_value = empty_history.to_structure(
        empty_history
    )

    HistoryCommand(
        clear=False, first=True, last=False, filter="missing"
    )._retrieve_conversation_filtered(filter="missing")
    captured = capsys.readouterr()
    assert "No history found.\n" in captured.out


def test_retrieve_conversation_filtered_success(
    mock_proxy, sample_history_entry, capsys
):
    """Test retrieving last conversation successfully."""
    mock_proxy.GetFilteredConversation.return_value = sample_history_entry.to_structure(
        sample_history_entry
    )

    HistoryCommand(
        clear=False, first=False, last=True, filter="test"
    )._retrieve_conversation_filtered(filter="missing")
    captured = capsys.readouterr()
    mock_proxy.GetFilteredConversation.assert_called_once()
    assert (
        "\x1b[92mQuery: test query\x1b[0m\n\x1b[94mAnswer: test response\x1b[0m\n"
        in captured.out
    )


def test_retrieve_first_conversation_success(mock_proxy, sample_history_entry, capsys):
    """Test retrieving first conversation successfully."""
    mock_proxy.GetFirstConversation.return_value = sample_history_entry.to_structure(
        sample_history_entry
    )

    HistoryCommand(clear=False, first=True, last=False)._retrieve_first_conversation()
    captured = capsys.readouterr()
    mock_proxy.GetFirstConversation.assert_called_once()
    assert (
        "\x1b[92mQuery: test query\x1b[0m\n\x1b[94mAnswer: test response\x1b[0m\n"
        in captured.out
    )


def test_retrieve_first_conversation_empty(mock_proxy, capsys):
    """Test retrieving first conversation when history is empty."""
    empty_history = HistoryEntry()
    mock_proxy.GetFirstConversation.return_value = empty_history.to_structure(
        empty_history
    )

    HistoryCommand(clear=False, first=True, last=False)._retrieve_first_conversation()
    captured = capsys.readouterr()
    assert "No history found.\n" in captured.out


def test_retrieve_last_conversation_success(mock_proxy, sample_history_entry, capsys):
    """Test retrieving last conversation successfully."""
    mock_proxy.GetLastConversation.return_value = sample_history_entry.to_structure(
        sample_history_entry
    )

    HistoryCommand(clear=False, first=False, last=True)._retrieve_last_conversation()
    captured = capsys.readouterr()
    mock_proxy.GetLastConversation.assert_called_once()
    assert (
        "\x1b[92mQuery: test query\x1b[0m\n\x1b[94mAnswer: test response\x1b[0m\n"
        in captured.out
    )


def test_retrieve_last_conversation_empty(mock_proxy, capsys):
    """Test retrieving last conversation when history is empty."""
    empty_history = HistoryEntry()
    mock_proxy.GetLastConversation.return_value = empty_history.to_structure(
        empty_history
    )

    HistoryCommand(clear=False, first=False, last=True)._retrieve_last_conversation()
    captured = capsys.readouterr()
    assert "No history found.\n" in captured.out


def test_clear_history_success(mock_proxy, capsys):
    """Test clearing history successfully."""
    HistoryCommand(clear=True, first=False, last=False)._clear_history()
    captured = capsys.readouterr()
    assert "Cleaning the history" in captured.out
    mock_proxy.ClearHistory.assert_called_once()
