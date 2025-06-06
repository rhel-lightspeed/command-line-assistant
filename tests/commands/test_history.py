from argparse import Namespace
from datetime import datetime

import pytest

from command_line_assistant.commands.history import history_command
from command_line_assistant.dbus.exceptions import (
    HistoryNotAvailableError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.structures.chat import ChatEntry, ChatList
from command_line_assistant.dbus.structures.history import HistoryEntry, HistoryList
from command_line_assistant.utils.cli import CommandContext


@pytest.fixture
def default_namespace():
    return Namespace(
        first=False,
        last=False,
        clear=False,
        clear_all=False,
        filter=None,
        all=False,
        from_chat="default",
        plain=True,
    )


@pytest.fixture
def command_context():
    return CommandContext()


@pytest.fixture
def sample_history_entry():
    """Create a sample history entry for testing."""
    entry = HistoryEntry("test query", "test response", "test", str(datetime.now()))
    last = HistoryEntry(
        "test final query", "test final response", "test", str(datetime.now())
    )
    history_entry = HistoryList([entry, last])
    return history_entry


def test_history_command_all_success(
    mock_dbus_service, sample_history_entry, default_namespace, command_context, capsys
):
    """Test retrieving all conversations successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetHistory.return_value = sample_history_entry.structure()

    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Getting all conversations from history" in captured.out
    assert "test query" in captured.out
    assert "test response" in captured.out


def test_history_command_all_not_available(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test retrieving all conversations when history not available."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetHistory.side_effect = HistoryNotAvailableError(
        "History not found"
    )

    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 82  # HistoryCommandException code
    assert (
        "Looks like no history was found. Try asking something first!" in captured.err
    )


def test_history_command_all_not_enabled(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test retrieving all conversations when history not enabled."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetHistory.side_effect = HistoryNotEnabledError(
        "History disabled"
    )

    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 82
    assert "Looks like history is not enabled yet" in captured.err


def test_history_command_first_success(
    mock_dbus_service, sample_history_entry, default_namespace, command_context, capsys
):
    """Test retrieving first conversation successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetFirstConversation.return_value = (
        sample_history_entry.structure()
    )

    default_namespace.first = True
    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Getting first conversation from history" in captured.out
    assert "test query" in captured.out


def test_history_command_last_success(
    mock_dbus_service, sample_history_entry, default_namespace, command_context, capsys
):
    """Test retrieving last conversation successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetLastConversation.return_value = (
        sample_history_entry.structure()
    )

    default_namespace.last = True
    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Getting last conversation from history" in captured.out
    assert "test query" in captured.out


def test_history_command_filter_success(
    mock_dbus_service, sample_history_entry, default_namespace, command_context, capsys
):
    """Test filtering conversation history successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetFilteredConversation.return_value = (
        sample_history_entry.structure()
    )

    default_namespace.filter = "test"
    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Filtering conversation history" in captured.out
    assert "test query" in captured.out


def test_history_command_clear_success(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test clearing history successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.IsChatAvailable.return_value = True
    mock_dbus_service.ClearHistory.return_value = None

    default_namespace.clear = True
    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Cleaning the history" in captured.out


def test_history_command_clear_chat_not_available(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test clearing history when chat is not available."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.IsChatAvailable.return_value = False

    default_namespace.clear = True
    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 82
    assert "Nothing to clean as default chat is not available" in captured.err


def test_history_command_clear_all_success(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test clearing all history successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetAllChatFromUser.return_value = ChatList(
        [ChatEntry(name="test", description="test", created_at=str(datetime.now()))]
    ).structure()
    mock_dbus_service.ClearAllHistory.return_value = None

    default_namespace.clear_all = True
    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Cleaning the history" in captured.out


def test_history_command_clear_all_no_chats(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test clearing all history when no chats exist."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetAllChatFromUser.return_value = ChatList([]).structure()

    default_namespace.clear_all = True
    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 82
    assert "Nothing to clean as there is no chat session in place" in captured.err


def test_history_command_empty_history(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test handling empty history response."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetHistory.return_value = HistoryList([]).structure()

    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "No history entries found" in captured.out


def test_history_command_custom_chat(
    mock_dbus_service, sample_history_entry, default_namespace, command_context, capsys
):
    """Test history command with custom chat name."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetFirstConversation.return_value = (
        sample_history_entry.structure()
    )

    default_namespace.first = True
    default_namespace.from_chat = "custom-chat"
    result = history_command(default_namespace, command_context)

    assert result == 0
    mock_dbus_service.GetFirstConversation.assert_called_with(
        "test-user", "custom-chat"
    )


def test_history_command_plain_mode(
    mock_dbus_service, sample_history_entry, command_context, capsys
):
    """Test history command in plain mode."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetHistory.return_value = sample_history_entry.structure()

    args = Namespace(
        first=False,
        last=False,
        clear=False,
        clear_all=False,
        filter=None,
        all=False,
        from_chat="default",
        plain=True,
    )
    result = history_command(args, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "test query" in captured.out


def test_history_command_multiple_entries(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test history command with multiple entries."""
    entries = HistoryList(
        [
            HistoryEntry("query 1", "response 1", "test", str(datetime.now())),
            HistoryEntry("query 2", "response 2", "test", str(datetime.now())),
        ]
    )

    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetHistory.return_value = entries.structure()

    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "query 1" in captured.out
    assert "response 1" in captured.out
    assert "query 2" in captured.out
    assert "response 2" in captured.out
    # Should have separator between entries
    assert "═" in captured.out


@pytest.mark.parametrize(
    ("operation", "namespace_attr"),
    [
        ("first", "first"),
        ("last", "last"),
        ("clear", "clear"),
        ("clear_all", "clear_all"),
    ],
)
def test_history_operations_with_history_disabled(
    mock_dbus_service,
    operation,
    namespace_attr,
    default_namespace,
    command_context,
    capsys,
):
    """Test all operations with history disabled."""
    mock_dbus_service.GetUserId.return_value = "test-user"

    # Set up different exceptions for different operations
    if operation == "clear":
        mock_dbus_service.IsChatAvailable.return_value = True
        mock_dbus_service.ClearHistory.side_effect = HistoryNotEnabledError(
            "History disabled"
        )
    elif operation == "clear_all":
        mock_dbus_service.GetAllChatFromUser.return_value = ChatList(
            [ChatEntry(name="test", description="test", created_at=str(datetime.now()))]
        ).structure()
        mock_dbus_service.ClearAllHistory.side_effect = HistoryNotEnabledError(
            "History disabled"
        )
    else:
        getattr(
            mock_dbus_service, f"Get{operation.title()}Conversation"
        ).side_effect = HistoryNotEnabledError("History disabled")

    setattr(default_namespace, namespace_attr, True)
    result = history_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 82
    assert "Looks like history is not enabled yet" in captured.err
