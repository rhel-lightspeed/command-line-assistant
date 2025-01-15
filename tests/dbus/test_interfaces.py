from unittest.mock import patch

import pytest
from dasbus.server.template import InterfaceTemplate

from command_line_assistant.dbus.interfaces import (
    HistoryInterface,
    QueryInterface,
)
from command_line_assistant.dbus.structures import HistoryEntry, Message
from command_line_assistant.history.manager import HistoryManager
from command_line_assistant.history.plugins.local import LocalHistory


@pytest.fixture
def mock_history_entry(mock_config):
    manager = HistoryManager(mock_config, 1000, LocalHistory)
    return manager


@pytest.fixture
def query_interface(mock_context):
    """Create a QueryInterface instance with mock implementation."""
    interface = QueryInterface(mock_context)
    assert isinstance(interface, InterfaceTemplate)
    return interface


@pytest.fixture
def history_interface(mock_context):
    """Create a HistoryInterface instance with mock implementation."""
    interface = HistoryInterface(mock_context)
    assert isinstance(interface, InterfaceTemplate)
    return interface


def test_query_interface_ask_question(query_interface, mock_config):
    """Test retrieving answer from query interface."""
    expected_response = "test response"
    with patch(
        "command_line_assistant.dbus.interfaces.submit", return_value=expected_response
    ) as mock_submit:
        response = query_interface.AskQuestion(
            "b7e95c2c-d2a8-11ef-a6bf-52b437312584", "test?"
        )

        mock_submit.assert_called_once_with("test?", mock_config)

        reconstructed = Message.from_structure(response)
        assert reconstructed.message == expected_response


def test_history_interface_get_history(history_interface, mock_history_entry):
    """Test getting all history through history interface."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write("test query", "test response")
        response = history_interface.GetHistory(1000)

        reconstructed = HistoryEntry.from_structure(response)
        assert len(reconstructed.entries) == 1
        assert reconstructed.entries[0].query == "test query"
        assert reconstructed.entries[0].response == "test response"


def test_history_interface_get_first_conversation(
    history_interface, mock_history_entry
):
    """Test getting first conversation through history interface."""

    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write("test query", "test response")
        manager.write("test query2", "test response2")
        manager.write("test query3", "test response3")
        response = history_interface.GetFirstConversation(1000)

        reconstructed = HistoryEntry.from_structure(response)
        assert len(reconstructed.entries) == 1
        assert reconstructed.entries[0].query == "test query"
        assert reconstructed.entries[0].response == "test response"


def test_history_interface_get_last_conversation(history_interface, mock_history_entry):
    """Test getting first conversation through history interface."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write("test query", "test response")
        manager.write("test query2", "test response2")
        manager.write("test query3", "test response3")
        response = history_interface.GetLastConversation(1000)

        reconstructed = HistoryEntry.from_structure(response)
        assert len(reconstructed.entries) == 1
        assert reconstructed.entries[0].query == "test query3"
        assert reconstructed.entries[0].response == "test response3"


def test_history_interface_get_filtered_conversation(
    history_interface, mock_history_entry
):
    """Test getting filtered conversation through history interface."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write("test query", "test response")
        manager.write("not a query", "not a response")
        response = history_interface.GetFilteredConversation(1000, filter="test")

        reconstructed = HistoryEntry.from_structure(response)
        assert len(reconstructed.entries) == 1
        assert reconstructed.entries[0].query == "test query"
        assert reconstructed.entries[0].response == "test response"


def test_history_interface_get_filtered_conversation_duplicate_entries_not_matching(
    history_interface, mock_history_entry
):
    """Test getting filtered conversation through duplicated history interface.

    This test will have a duplicated entry, but not matching the "id". This should be enough to be considered a new entry
    """
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write("test query", "test response")
        manager.write("test query", "test response")
        response = history_interface.GetFilteredConversation(1000, filter="test")

        reconstructed = HistoryEntry.from_structure(response)
        assert len(reconstructed.entries) == 2
        assert reconstructed.entries[0].query == "test query"
        assert reconstructed.entries[0].response == "test response"


def test_history_interface_clear_history(history_interface):
    """Test clearing history through history interface."""
    with patch("command_line_assistant.dbus.interfaces.HistoryManager") as mock_manager:
        history_interface.ClearHistory(1000)
        mock_manager.return_value.clear.assert_called_once()


def test_history_interface_empty_history(history_interface):
    """Test handling empty history in all methods."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ):
        # Test all methods with empty history
        for method in [
            history_interface.GetHistory,
            history_interface.GetFirstConversation,
            history_interface.GetLastConversation,
        ]:
            response = method(1000)
            reconstructed = HistoryEntry.from_structure(response)
            assert len(reconstructed.entries) == 0
