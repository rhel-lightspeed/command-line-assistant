from unittest.mock import patch

import pytest

from command_line_assistant.commands.history import (
    HistoryCommand,
)
from command_line_assistant.dbus.exceptions import (
    ChatNotFoundError,
    CorruptedHistoryError,
    HistoryNotAvailable,
    MissingHistoryFileError,
)
from command_line_assistant.dbus.structures.history import HistoryEntry, HistoryList


# Mock the entire DBus service/constants module
@pytest.fixture(autouse=True)
def mock_dbus_service(mock_proxy):
    """Fixture to mock DBus service and automatically use it for all tests"""
    with (
        patch(
            "command_line_assistant.commands.history.HISTORY_IDENTIFIER"
        ) as mock_service,
        patch("command_line_assistant.commands.history.USER_IDENTIFIER"),
        patch("command_line_assistant.commands.history.CHAT_IDENTIFIER"),
    ):
        # Create a mock proxy that will be returned by get_proxy()
        mock_service.get_proxy.return_value = mock_proxy

        yield mock_proxy


@pytest.fixture
def sample_history_entry():
    """Create a sample history entry for testing."""
    entry = HistoryEntry("test query", "test response", "2024-01-01T00:00:00Z")
    last = HistoryEntry(
        "test final query", "test final response", "2024-01-02T00:00:00Z"
    )
    history_entry = HistoryList([entry, last])
    return history_entry


def test_retrieve_all_conversations_success(mock_proxy, sample_history_entry, capsys):
    """Test retrieving all conversations successfully."""
    mock_proxy.GetHistory.return_value = sample_history_entry.to_structure(
        sample_history_entry
    )

    HistoryCommand(clear=False, first=False, last=False).run()

    captured = capsys.readouterr()
    assert "Getting all conversations from history" in captured.out
    mock_proxy.GetHistory.assert_called_once()


def test_retrieve_conversation_filtered_success(
    mock_proxy, sample_history_entry, capsys
):
    """Test retrieving last conversation successfully."""
    mock_proxy.GetFilteredConversation.return_value = sample_history_entry.structure()

    HistoryCommand(clear=False, first=False, last=False, filter="missing").run()
    captured = capsys.readouterr()
    mock_proxy.GetFilteredConversation.assert_called_once()
    assert (
        "\x1b[92mQuestion: test query\x1b[0m\n\x1b[94mAnswer: test response\x1b[0m\n"
        in captured.out
    )


def test_retrieve_first_conversation_success(mock_proxy, sample_history_entry, capsys):
    """Test retrieving first conversation successfully."""
    mock_proxy.GetFirstConversation.return_value = sample_history_entry.structure()

    HistoryCommand(clear=False, first=True, last=False).run()
    captured = capsys.readouterr()
    mock_proxy.GetFirstConversation.assert_called_once()
    assert (
        "\x1b[92mQuestion: test query\x1b[0m\n\x1b[94mAnswer: test response\x1b[0m\n"
        in captured.out
    )


def test_retrieve_last_conversation_success(mock_proxy, sample_history_entry, capsys):
    """Test retrieving last conversation successfully."""
    mock_proxy.GetLastConversation.return_value = sample_history_entry.structure()

    HistoryCommand(clear=False, first=False, last=True).run()
    captured = capsys.readouterr()
    mock_proxy.GetLastConversation.assert_called_once()
    assert (
        "\x1b[92mQuestion: test query\x1b[0m\n\x1b[94mAnswer: test response\x1b[0m\n"
        in captured.out
    )


def test_clear_history_success(mock_proxy, capsys):
    """Test clearing history successfully."""
    HistoryCommand(clear=True, first=False, last=False).run()
    captured = capsys.readouterr()
    assert "Cleaning the history" in captured.out
    mock_proxy.ClearHistory.assert_called_once()


@pytest.mark.parametrize(
    ("query", "response", "expected"),
    (
        (
            "test",
            "test",
            "\x1b[92mQuestion: test\x1b[0m\n\x1b[94mAnswer: test\x1b[0m\nTime:\n",
        ),
    ),
)
def test_show_history(query, response, expected, capsys):
    HistoryCommand(clear=False, first=False, last=False)._show_history(
        HistoryList([HistoryEntry(query, response)])
    )

    captured = capsys.readouterr()
    assert expected in captured.out


@pytest.mark.parametrize(
    ("exception", "expected_msg"),
    (
        (MissingHistoryFileError("missing history"), "missing history"),
        (CorruptedHistoryError("corrupted history"), "corrupted history"),
        (ChatNotFoundError("chat not found"), "chat not found"),
        (HistoryNotAvailable("history not available"), "history not available"),
    ),
)
def test_history_run_exceptions(exception, expected_msg, mock_proxy, capsys):
    mock_proxy.GetHistory.side_effect = exception

    result = HistoryCommand(clear=False, first=False, last=False, filter=None).run()

    captured = capsys.readouterr()
    assert result == 1
    assert expected_msg in captured.err
