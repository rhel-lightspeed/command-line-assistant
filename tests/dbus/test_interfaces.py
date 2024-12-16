from unittest.mock import Mock, patch

import pytest

from command_line_assistant.config import Config
from command_line_assistant.dbus.interfaces import (
    HistoryInterface,
    Message,
    QueryInterface,
)
from command_line_assistant.dbus.structures import HistoryEntry


@pytest.fixture
def mock_implementation():
    impl = Mock()
    impl.config = Mock(spec=Config)
    impl.config.history = Mock()
    impl.query = Mock()
    return impl


@pytest.fixture
def query_interface(mock_implementation):
    interface = QueryInterface(mock_implementation)
    interface.watch_property = Mock()
    return interface


class TestQueryInterface:
    def test_connect_signals(self, query_interface, mock_implementation):
        query_interface.connect_signals()
        query_interface.watch_property.assert_called_once_with(
            "RetrieveAnswer", mock_implementation.query_changed
        )

    @patch("command_line_assistant.dbus.interfaces.submit")
    def test_retrieve_answer_success(
        self, mock_submit, query_interface, mock_implementation
    ):
        mock_submit.return_value = "test response"
        mock_implementation.query.message = "test query"

        result = query_interface.RetrieveAnswer

        mock_submit.assert_called_once_with("test query", mock_implementation.config)
        message = Message.from_structure(result)
        assert message.message == "test response"

    @patch("command_line_assistant.dbus.interfaces.submit")
    def test_retrieve_answer_empty_query(
        self, mock_submit, query_interface, mock_implementation
    ):
        mock_submit.return_value = ""
        mock_implementation.query.message = ""

        result = query_interface.RetrieveAnswer

        mock_submit.assert_called_once_with("", mock_implementation.config)
        message = Message.from_structure(result)
        assert message.message == ""

    def test_process_query(self, query_interface, mock_implementation):
        test_query = Message()
        test_query.message = "test message"
        query_structure = Message.to_structure(test_query)

        query_interface.ProcessQuery(query_structure)

        mock_implementation.process_query.assert_called_once()
        processed_message = mock_implementation.process_query.call_args[0][0]
        assert isinstance(processed_message, Message)
        assert processed_message.message == "test message"


class TestHistoryInterface:
    @pytest.fixture
    def history_interface(self, mock_implementation):
        return HistoryInterface(mock_implementation)

    @patch("command_line_assistant.dbus.interfaces.handle_history_read")
    def test_get_history_success(
        self, mock_history_read, history_interface, mock_implementation
    ):
        test_entries = ["entry1", "entry2"]
        mock_history_read.return_value = test_entries

        result = history_interface.GetHistory

        mock_history_read.assert_called_once_with(mock_implementation.config)
        history = HistoryEntry.from_structure(result)
        assert history.entries == test_entries

    @patch("command_line_assistant.dbus.interfaces.handle_history_read")
    def test_get_history_empty(
        self, mock_history_read, history_interface, mock_implementation
    ):
        mock_history_read.return_value = []

        result = history_interface.GetHistory

        mock_history_read.assert_called_once_with(mock_implementation.config)
        history = HistoryEntry.from_structure(result)
        assert history.entries == []

    @patch("command_line_assistant.dbus.interfaces.handle_history_write")
    def test_clear_history(
        self, mock_history_write, history_interface, mock_implementation
    ):
        history_interface.ClearHistory()

        mock_history_write.assert_called_once_with(
            mock_implementation.config.history.file, [], ""
        )

    @patch("command_line_assistant.dbus.interfaces.handle_history_write")
    def test_clear_history_with_nonexistent_file(
        self, mock_history_write, history_interface, mock_implementation
    ):
        mock_implementation.config.history.file = "/nonexistent/path"

        history_interface.ClearHistory()

        mock_history_write.assert_called_once_with("/nonexistent/path", [], "")
