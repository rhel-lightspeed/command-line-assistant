import json
from unittest.mock import Mock, patch

import pytest
from dasbus.server.template import InterfaceTemplate

from command_line_assistant.dbus.interfaces import (
    HistoryInterface,
    QueryInterface,
)
from command_line_assistant.dbus.structures import HistoryEntry, Message
from command_line_assistant.history.schemas import History


@pytest.fixture
def mock_implementation(mock_config):
    """Create a mock implementation with configuration."""
    impl = Mock()
    impl.config = mock_config
    mock_query = Message()
    mock_query.message = "test query"
    impl.query = mock_query
    return impl


@pytest.fixture
def query_interface(mock_implementation):
    """Create a QueryInterface instance with mock implementation."""
    interface = QueryInterface(mock_implementation)
    assert isinstance(interface, InterfaceTemplate)
    return interface


@pytest.fixture
def history_interface(mock_implementation):
    """Create a HistoryInterface instance with mock implementation."""
    interface = HistoryInterface(mock_implementation)
    assert isinstance(interface, InterfaceTemplate)
    return interface


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


def test_query_interface_retrieve_answer(query_interface, mock_implementation):
    """Test retrieving answer from query interface."""
    expected_response = "test response"
    mock_implementation.config.history.file.parent.mkdir()
    mock_implementation.config.history.file.write_text(History().to_json())
    with patch(
        "command_line_assistant.dbus.interfaces.submit", return_value=expected_response
    ) as mock_submit:
        response = query_interface.RetrieveAnswer()

        mock_submit.assert_called_once_with(
            mock_implementation.query.message, mock_implementation.config
        )

        reconstructed = Message.from_structure(response)
        assert reconstructed.message == expected_response


def test_query_interface_process_query(query_interface, mock_implementation):
    """Test processing query through query interface."""
    test_query = Message()
    test_query.message = "test query"

    query_interface.ProcessQuery(Message.to_structure(test_query))

    mock_implementation.process_query.assert_called_once()
    processed_query = mock_implementation.process_query.call_args[0][0]
    assert isinstance(processed_query, Message)
    assert processed_query.message == test_query.message


def test_history_interface_get_history(
    history_interface, mock_implementation, sample_history_data
):
    """Test getting all history through history interface."""
    mock_history = History.from_json(json.dumps(sample_history_data))

    with patch("command_line_assistant.dbus.interfaces.HistoryManager") as mock_manager:
        mock_manager.return_value.read.return_value = mock_history
        response = history_interface.GetHistory()

        reconstructed = HistoryEntry.from_structure(response)
        assert len(reconstructed.entries) == 1
        assert reconstructed.entries[0].query == "test query"
        assert reconstructed.entries[0].response == "test response"


def test_history_interface_get_first_conversation(
    history_interface, mock_implementation, sample_history_data
):
    """Test getting first conversation through history interface."""
    mock_history = History.from_json(json.dumps(sample_history_data))

    with patch("command_line_assistant.dbus.interfaces.HistoryManager") as mock_manager:
        mock_manager.return_value.read.return_value = mock_history
        response = history_interface.GetFirstConversation()

        reconstructed = HistoryEntry.from_structure(response)
        assert len(reconstructed.entries) == 1
        assert reconstructed.entries[0].query == "test query"
        assert reconstructed.entries[0].response == "test response"


def test_history_interface_get_last_conversation(
    history_interface, mock_implementation, sample_history_data
):
    """Test getting first conversation through history interface."""
    mock_history = History.from_json(json.dumps(sample_history_data))

    with patch("command_line_assistant.dbus.interfaces.HistoryManager") as mock_manager:
        mock_manager.return_value.read.return_value = mock_history
        response = history_interface.GetLastConversation()

        reconstructed = HistoryEntry.from_structure(response)
        assert len(reconstructed.entries) == 1
        assert reconstructed.entries[0].query == "test query"
        assert reconstructed.entries[0].response == "test response"


def test_history_interface_clear_history(history_interface):
    """Test clearing history through history interface."""
    with patch("command_line_assistant.dbus.interfaces.HistoryManager") as mock_manager:
        history_interface.ClearHistory()
        mock_manager.return_value.clear.assert_called_once()


def test_history_interface_empty_history(history_interface, mock_implementation):
    """Test handling empty history in all methods."""
    empty_history = History()

    with patch("command_line_assistant.dbus.interfaces.HistoryManager") as mock_manager:
        mock_manager.return_value.read.return_value = empty_history

        # Test all methods with empty history
        for method in [
            history_interface.GetHistory,
            history_interface.GetFirstConversation,
            history_interface.GetLastConversation,
        ]:
            response = method()
            reconstructed = HistoryEntry.from_structure(response)
            assert len(reconstructed.entries) == 0
