from argparse import Namespace
from datetime import datetime

import pytest

from command_line_assistant.commands import history
from command_line_assistant.dbus.exceptions import (
    HistoryNotAvailableError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.structures.chat import ChatEntry, ChatList
from command_line_assistant.dbus.structures.history import HistoryEntry, HistoryList
from command_line_assistant.exceptions import HistoryCommandException
from command_line_assistant.utils.cli import CommandContext
from command_line_assistant.utils.dbus import DbusUtils
from command_line_assistant.utils.renderers import RenderUtils


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
def mock_user_chat_list():
    return ChatList(
        [ChatEntry(name="test", description="test", created_at=str(datetime.now()))]
    ).structure()


@pytest.fixture
def sample_history_entry():
    """Create a sample history entry for testing."""
    entry = HistoryEntry("test query", "test response", "test", str(datetime.now()))
    last = HistoryEntry(
        "test final query", "test final response", "test", str(datetime.now())
    )
    history_entry = HistoryList([entry, last])
    return history_entry


def test_history_command_all_success(mock_dbus_service, sample_history_entry, capsys):
    """Test retrieving all conversations successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetHistory.return_value = sample_history_entry.structure()

    result = history._all_history(RenderUtils(True), DbusUtils(), "test-user", True)

    captured = capsys.readouterr()
    assert result == 0
    assert "Getting all conversations from history" in captured.out
    assert "test query" in captured.out
    assert "test response" in captured.out


def test_history_command_all_not_available(mock_dbus_service):
    """Test retrieving all conversations when history not available."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetHistory.side_effect = HistoryNotAvailableError(
        "Looks like no history was found. Try asking something first!"
    )

    with pytest.raises(
        HistoryCommandException,
        match="Looks like no history was found. Try asking something first!",
    ):
        history._all_history(RenderUtils(True), DbusUtils(), "test-user", True)


def test_history_command_all_not_enabled(mock_dbus_service):
    """Test retrieving all conversations when history not enabled."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetHistory.side_effect = HistoryNotEnabledError(
        "Looks like history is not enabled yet"
    )

    with pytest.raises(
        HistoryCommandException, match="Looks like history is not enabled yet"
    ):
        history._all_history(RenderUtils(True), DbusUtils(), "test-user", True)


def test_history_command_first_success(
    mock_dbus_service, sample_history_entry, default_namespace, capsys
):
    """Test retrieving first conversation successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetFirstConversation.return_value = (
        sample_history_entry.structure()
    )

    default_namespace.first = True
    result = history._first_history(
        RenderUtils(True), DbusUtils(), "test-user", "test", True
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "Getting first conversation from history" in captured.out
    assert "test query" in captured.out


def test_history_command_last_success(
    mock_dbus_service, sample_history_entry, default_namespace, capsys
):
    """Test retrieving last conversation successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetLastConversation.return_value = (
        sample_history_entry.structure()
    )

    default_namespace.last = True
    result = history._last_history(
        RenderUtils(True), DbusUtils(), "test-user", "test", True
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "Getting last conversation from history" in captured.out
    assert "test query" in captured.out


def test_history_command_filter_success(
    mock_dbus_service, sample_history_entry, default_namespace, capsys
):
    """Test filtering conversation history successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetFilteredConversation.return_value = (
        sample_history_entry.structure()
    )

    default_namespace.filter = "test"
    result = history._filter_history(
        RenderUtils(True), DbusUtils(), "test-user", "test", "test", True
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "Filtering conversation history" in captured.out
    assert "test query" in captured.out


def test_history_command_clear_success(mock_dbus_service, default_namespace, capsys):
    """Test clearing history successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.IsChatAvailable.return_value = True
    mock_dbus_service.ClearHistory.return_value = None

    default_namespace.clear = True
    result = history._clear_history(RenderUtils(True), DbusUtils(), "test-user", "test")

    captured = capsys.readouterr()
    assert result == 0
    assert "History cleaned successfully." in captured.out


def test_history_command_chat_not_available(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test clearing history when chat is not available."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.IsChatAvailable.return_value = False
    default_namespace.from_chat = "test"

    result = history.history_command.func(default_namespace, command_context)
    captured = capsys.readouterr()
    assert result == 82
    assert (
        "Nothing to clean as test chat is not available. Try asking something first."
        in captured.err
    )


def test_history_command_clear_all_success(
    mock_dbus_service, default_namespace, capsys, mock_user_chat_list
):
    """Test clearing all history successfully."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetAllChatFromUser.return_value = mock_user_chat_list
    mock_dbus_service.ClearAllHistory.return_value = None

    default_namespace.clear_all = True
    result = history._clear_all_history(RenderUtils(True), DbusUtils(), "test-user")

    captured = capsys.readouterr()
    assert result == 0
    assert "All histories cleared successfully." in captured.out


def test_history_command_clear_all_no_chats(mock_dbus_service, default_namespace):
    """Test clearing all history when no chats exist."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetAllChatFromUser.return_value = ChatList([]).structure()

    default_namespace.clear_all = True

    with pytest.raises(
        HistoryCommandException,
        match="Nothing to clean as there is no chat session in place.",
    ):
        history._clear_all_history(RenderUtils(True), DbusUtils(), "test-user")


def test_history_command_empty_history(capsys):
    """Test handling empty history response."""
    entries = HistoryList([])

    history._show_history(entries, True)

    captured = capsys.readouterr()
    assert "No history entries found" in captured.out


def test_history_command_custom_chat(mock_dbus_service, sample_history_entry):
    """Test history command with custom chat name."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetFirstConversation.return_value = (
        sample_history_entry.structure()
    )

    result = history._first_history(
        RenderUtils(True), DbusUtils(), "test-user", "custom-chat", True
    )

    assert result == 0
    mock_dbus_service.GetFirstConversation.assert_called_with(
        "test-user", "custom-chat"
    )


def test_history_command_plain_mode(
    mock_dbus_service, default_namespace, sample_history_entry, command_context, capsys
):
    """Test history command in plain mode."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetHistory.return_value = sample_history_entry.structure()

    result = history.history_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "test query" in captured.out


def test_history_command_multiple_entries(capsys):
    """Test history command with multiple entries."""
    entries = HistoryList(
        [
            HistoryEntry("query 1", "response 1", "test", str(datetime.now())),
            HistoryEntry("query 2", "response 2", "test", str(datetime.now())),
        ]
    )

    history._show_history(entries, True)

    captured = capsys.readouterr()
    assert "query 1" in captured.out
    assert "response 1" in captured.out
    assert "query 2" in captured.out
    assert "response 2" in captured.out
    # Should have separator between entries
    assert "═" in captured.out


@pytest.mark.parametrize(
    ("dbus_func", "namespace_attr"),
    [
        ("GetFirstConversation", "first"),
        ("GetLastConversation", "last"),
        ("GetFilteredConversation", "filter"),
        ("GetHistory", None),
        ("ClearHistory", "clear"),
        ("ClearAllHistory", "clear_all"),
    ],
)
def test_history_operations_with_history_disabled(
    mock_dbus_service,
    mock_user_chat_list,
    dbus_func,
    namespace_attr,
    default_namespace,
    command_context,
    capsys,
):
    """Test all operations with history disabled."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetAllChatFromUser.return_value = mock_user_chat_list
    exception_msg = "Looks like history is not enabled yet. Enable it in the configuration file before trying to access history."
    exception = HistoryNotEnabledError(exception_msg)

    def t(*args, **kwargs):
        raise exception

    setattr(mock_dbus_service, dbus_func, t)
    if namespace_attr:
        setattr(default_namespace, namespace_attr, True)

    result = history.history_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 82
    assert exception_msg in captured.err
