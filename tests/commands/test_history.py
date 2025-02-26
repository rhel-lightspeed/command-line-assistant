from argparse import Namespace
from datetime import datetime

import pytest

from command_line_assistant.commands.history import (
    AllHistoryOperation,
    BaseHistoryOperation,
    ClearHistoryOperation,
    FilteredHistoryOperation,
    FirstHistoryOperation,
    HistoryCommand,
    LastHistoryOperation,
    _command_factory,
)
from command_line_assistant.dbus.exceptions import (
    HistoryNotAvailableError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.structures.history import HistoryEntry, HistoryList
from command_line_assistant.exceptions import (
    HistoryCommandException,
)
from command_line_assistant.utils.renderers import create_text_renderer


@pytest.fixture
def sample_history_entry():
    """Create a sample history entry for testing."""
    entry = HistoryEntry("test query", "test response", str(datetime.now()))
    last = HistoryEntry("test final query", "test final response", str(datetime.now()))
    history_entry = HistoryList([entry, last])
    return history_entry


@pytest.fixture
def default_namespace():
    return Namespace(first=False, last=False, clear=False, filter="", all=False)


def test_retrieve_all_conversations_success(
    mock_dbus_service, sample_history_entry, capsys, default_kwargs
):
    """Test retrieving all conversations successfully."""
    mock_dbus_service.GetHistory.return_value = sample_history_entry.to_structure(
        sample_history_entry
    )
    default_kwargs["text_renderer"] = create_text_renderer()

    AllHistoryOperation(**default_kwargs).execute()

    captured = capsys.readouterr()
    assert "Getting all conversations from history" in captured.out
    mock_dbus_service.GetHistory.assert_called_once()


def test_retrieve_all_conversations_exception(mock_dbus_service, default_kwargs):
    """Test retrieving all conversations successfully."""
    mock_dbus_service.GetHistory.side_effect = HistoryNotAvailableError(
        "History not found"
    )
    with pytest.raises(
        HistoryCommandException,
        match="Looks like no history was found. Try asking something first!",
    ):
        AllHistoryOperation(**default_kwargs).execute()


def test_retrieve_conversation_filtered_success(
    mock_dbus_service, sample_history_entry, capsys, default_kwargs, default_namespace
):
    """Test retrieving last conversation successfully."""
    mock_dbus_service.GetFilteredConversation.return_value = (
        sample_history_entry.structure()
    )
    default_kwargs["text_renderer"] = create_text_renderer()
    default_namespace.filter = "missing"
    default_kwargs["args"] = default_namespace

    FilteredHistoryOperation(**default_kwargs).execute()

    captured = capsys.readouterr()
    mock_dbus_service.GetFilteredConversation.assert_called_once()
    assert "Question\n───────────\ntest query" in captured.out
    assert "Answer\n─────────\ntest response" in captured.out


def test_retrieve_conversation_filtered_exception(
    mock_dbus_service, default_kwargs, default_namespace
):
    """Test catching filtered conversation successfully."""
    default_namespace.filter = "missing"
    default_kwargs["args"] = default_namespace
    mock_dbus_service.GetFilteredConversation.side_effect = HistoryNotAvailableError(
        "History not found"
    )
    with pytest.raises(
        HistoryCommandException,
        match="Looks like no history was found. Try asking something first!",
    ):
        FilteredHistoryOperation(**default_kwargs).execute()


def test_retrieve_first_conversation_success(
    mock_dbus_service,
    sample_history_entry,
    capsys,
    default_kwargs,
):
    """Test retrieving first conversation successfully."""
    mock_dbus_service.GetFirstConversation.return_value = (
        sample_history_entry.structure()
    )
    default_kwargs["text_renderer"] = create_text_renderer()
    FirstHistoryOperation(**default_kwargs).execute()
    captured = capsys.readouterr()
    mock_dbus_service.GetFirstConversation.assert_called_once()
    assert "Question\n───────────\ntest query" in captured.out
    assert "Answer\n─────────\ntest response" in captured.out


def test_retrieve_first_conversation_exception(mock_dbus_service, default_kwargs):
    """Test catching first conversation successfully."""
    mock_dbus_service.GetFirstConversation.side_effect = HistoryNotAvailableError(
        "Not found history"
    )
    with pytest.raises(
        HistoryCommandException,
        match="Looks like no history was found. Try asking something first!",
    ):
        FirstHistoryOperation(**default_kwargs).execute()


def test_retrieve_last_conversation_success(
    mock_dbus_service, sample_history_entry, capsys, default_kwargs
):
    """Test retrieving last conversation successfully."""
    mock_dbus_service.GetLastConversation.return_value = (
        sample_history_entry.structure()
    )
    default_kwargs["text_renderer"] = create_text_renderer()
    LastHistoryOperation(**default_kwargs).execute()

    captured = capsys.readouterr()
    mock_dbus_service.GetLastConversation.assert_called_once()
    assert "Question\n───────────\ntest query" in captured.out
    assert "Answer\n─────────\ntest response" in captured.out


def test_retrieve_last_conversation_exception(mock_dbus_service, default_kwargs):
    """Test retrieving last conversation successfully."""
    mock_dbus_service.GetLastConversation.side_effect = HistoryNotAvailableError(
        "Not found history"
    )
    with pytest.raises(
        HistoryCommandException,
        match="Looks like no history was found. Try asking something first!",
    ):
        LastHistoryOperation(**default_kwargs).execute()


def test_clear_history_success(mock_dbus_service, capsys, default_kwargs):
    """Test clearing history successfully."""
    default_kwargs["text_renderer"] = create_text_renderer()
    ClearHistoryOperation(**default_kwargs).execute()
    captured = capsys.readouterr()
    assert "Cleaning the history" in captured.out
    mock_dbus_service.ClearHistory.assert_called_once()


def test_clear_history_exception(mock_dbus_service, default_kwargs):
    """Test clearing history successfully."""
    mock_dbus_service.ClearHistory.side_effect = HistoryNotAvailableError(
        "Not found history"
    )
    with pytest.raises(
        HistoryCommandException,
        match="Looks like no history was found. Try asking something first!",
    ):
        ClearHistoryOperation(**default_kwargs).execute()


def test_show_history(default_kwargs, capsys):
    default_kwargs["text_renderer"] = create_text_renderer()
    bash_history_operation = BaseHistoryOperation(**default_kwargs)
    bash_history_operation._show_history(
        HistoryList([HistoryEntry("test", "test", str(datetime.now()))])
    )

    captured = capsys.readouterr()
    assert "Question\n───────────\ntest" in captured.out
    assert "Answer\n─────────\ntest" in captured.out


@pytest.mark.parametrize(
    ("exception", "expected_msg"),
    ((HistoryCommandException("missing history"), "missing history"),),
)
def test_history_run_exceptions(exception, expected_msg, mock_dbus_service, capsys):
    mock_dbus_service.GetFirstConversation.side_effect = exception
    args = Namespace(filter="", clear=False, first=True, last=False)
    result = HistoryCommand(args).run()

    captured = capsys.readouterr()
    assert result == 1
    assert expected_msg in captured.err


def test_history_empty_response(mock_dbus_service, capsys):
    """Test handling empty history response"""
    mock_dbus_service.GetFirstConversation.return_value = HistoryList([]).structure()

    args = Namespace(filter="", clear=False, first=True, last=False)
    HistoryCommand(args).run()

    captured = capsys.readouterr()
    assert "No history entries found" in captured.out


@pytest.mark.parametrize(
    ("first", "last", "clear", "filter", "all"),
    (
        (
            True,
            False,
            False,
            "",
            False,
        ),
        (
            False,
            False,
            False,
            "test",
            False,
        ),
    ),
)
def test_command_factory(first, last, clear, filter, all, default_namespace):
    """Test _command_factory function"""
    default_namespace.first = first
    default_namespace.last = last
    default_namespace.clear = clear
    default_namespace.filter = filter
    default_namespace.all = all
    command = _command_factory(default_namespace)

    assert isinstance(command, HistoryCommand)
    assert command._args.first == first
    assert command._args.last == last
    assert command._args.clear == clear
    assert command._args.filter == filter
    assert command._args.all == all


@pytest.mark.parametrize(
    ("operation",),
    (
        (ClearHistoryOperation,),
        (FirstHistoryOperation,),
        (LastHistoryOperation,),
        (FilteredHistoryOperation,),
        (AllHistoryOperation,),
    ),
)
def test_operations_with_history_disabled(
    operation, default_kwargs, mock_dbus_service, caplog
):
    """Test all operations with history disabled"""
    mock_dbus_service.GetUserId.side_effect = HistoryNotEnabledError(
        "History not enabled"
    )
    default_kwargs["text_renderer"] = create_text_renderer()

    with pytest.raises(
        HistoryCommandException,
        match="Looks like history is not enabled yet. Enable it in the configuration file before trying to access history.",
    ):
        operation(**default_kwargs).execute()

    assert "History is not enabled. Nothing to do." in caplog.records[-1].message
