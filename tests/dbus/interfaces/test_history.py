from unittest.mock import patch

import pytest
from dasbus.server.template import InterfaceTemplate

from command_line_assistant.dbus.exceptions import HistoryNotAvailableError
from command_line_assistant.dbus.interfaces.history import HistoryInterface
from command_line_assistant.dbus.structures.history import HistoryList
from command_line_assistant.history.manager import HistoryManager
from command_line_assistant.history.plugins.local import LocalHistory


@pytest.fixture
def mock_history_entry(mock_config):
    manager = HistoryManager(mock_config, LocalHistory)
    return manager


@pytest.fixture
def history_interface(mock_context):
    """Create a HistoryInterface instance with mock implementation."""
    interface = HistoryInterface(mock_context)
    assert isinstance(interface, InterfaceTemplate)
    return interface


def test_history_interface_get_history(history_interface, mock_history_entry):
    """Test getting all history through history interface."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        uid = "1710e580-dfce-11ef-a98f-52b437312584"
        manager.write(
            uid,
            uid,
            "test query",
            "test response",
        )
        response = history_interface.GetHistory("1710e580-dfce-11ef-a98f-52b437312584")

        reconstructed = HistoryList.from_structure(response)
        assert len(reconstructed.histories) == 1
        assert reconstructed.histories[0].question == "test query"
        assert reconstructed.histories[0].response == "test response"


def test_history_interface_get_history_exception(history_interface):
    """Test getting all history through history interface."""
    uid = "1710e580-dfce-11ef-a98f-52b437312584"
    with pytest.raises(
        HistoryNotAvailableError, match="Unfortunately, no history was found."
    ):
        history_interface.GetHistory(uid)


def test_history_interface_get_first_conversation(
    history_interface, mock_history_entry
):
    """Test getting first conversation through history interface."""

    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        uid = "1710e580-dfce-11ef-a98f-52b437312584"
        manager.write(uid, uid, "test query", "test response")
        manager.write(uid, uid, "test query2", "test response2")
        manager.write(uid, uid, "test query3", "test response3")
        response = history_interface.GetFirstConversation(uid)

        reconstructed = HistoryList.from_structure(response)
        assert len(reconstructed.histories) == 1
        assert reconstructed.histories[0].question == "test query"
        assert reconstructed.histories[0].response == "test response"


def test_history_interface_get_first_conversation_exception(history_interface):
    uid = "1710e580-dfce-11ef-a98f-52b437312584"
    with pytest.raises(
        HistoryNotAvailableError, match="Unfortunately, no history was found."
    ):
        history_interface.GetFirstConversation(uid)


def test_history_interface_get_last_conversation(history_interface, mock_history_entry):
    """Test getting first conversation through history interface."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        uid = "1710e580-dfce-11ef-a98f-52b437312584"
        manager.write(uid, uid, "test query", "test response")
        manager.write(uid, uid, "test query2", "test response2")
        manager.write(uid, uid, "test query3", "test response3")
        response = history_interface.GetLastConversation(uid)

        reconstructed = HistoryList.from_structure(response)
        assert len(reconstructed.histories) == 1
        assert reconstructed.histories[0].question == "test query3"
        assert reconstructed.histories[0].response == "test response3"


def test_history_interface_get_last_conversation_exception(history_interface):
    uid = "1710e580-dfce-11ef-a98f-52b437312584"
    with pytest.raises(
        HistoryNotAvailableError, match="Unfortunately, no history was found."
    ):
        history_interface.GetLastConversation(uid)


def test_history_interface_get_filtered_conversation(
    history_interface, mock_history_entry
):
    """Test getting filtered conversation through history interface."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        uid = "1710e580-dfce-11ef-a98f-52b437312584"
        manager.write(uid, uid, "test query", "test response")
        manager.write(uid, uid, "not a query", "not a response")
        response = history_interface.GetFilteredConversation(uid, filter="test")

        reconstructed = HistoryList.from_structure(response)
        assert len(reconstructed.histories) == 1
        assert reconstructed.histories[0].question == "test query"
        assert reconstructed.histories[0].response == "test response"


def test_history_interface_get_filtered_conversation_exception(history_interface):
    uid = "1710e580-dfce-11ef-a98f-52b437312584"
    with pytest.raises(
        HistoryNotAvailableError, match="Unfortunately, no history was found."
    ):
        history_interface.GetFilteredConversation(uid, filter="test")


def test_history_interface_get_filtered_conversation_duplicate_entries_not_matching(
    history_interface, mock_history_entry
):
    """Test getting filtered conversation through duplicated history interface.

    This test will have a duplicated entry, but not matching the "id". This should be enough to be considered a new entry
    """
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        uid = "1710e580-dfce-11ef-a98f-52b437312584"
        manager.write(uid, uid, "test query", "test response")
        manager.write(uid, uid, "test query", "test response")
        response = history_interface.GetFilteredConversation(uid, filter="test")

        reconstructed = HistoryList.from_structure(response)
        assert len(reconstructed.histories) == 2
        assert reconstructed.histories[0].question == "test query"
        assert reconstructed.histories[0].response == "test response"


def test_history_interface_clear_history(history_interface, caplog):
    """Test clearing history through history interface."""
    with patch("command_line_assistant.dbus.interfaces.history.HistoryManager"):
        uid = "1710e580-dfce-11ef-a98f-52b437312584"
        history_interface.ClearHistory(uid)
        assert "Clearing history entries for user." in caplog.records[0].message


def test_history_interface_empty_history(mock_history_entry, history_interface):
    """Test handling empty history in all methods."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        uid = "1710e580-dfce-11ef-a98f-52b437312584"
        manager.write(uid, uid, "test query", "test response")
        # Test all methods with empty history
        for method in [
            history_interface.GetHistory,
            history_interface.GetFirstConversation,
            history_interface.GetLastConversation,
        ]:
            response = method("1710e580-dfce-11ef-a98f-52b437312584")
            reconstructed = HistoryList.from_structure(response)
            assert len(reconstructed.histories) == 1


def test_write_history(history_interface, caplog):
    with patch("command_line_assistant.dbus.interfaces.history.HistoryManager"):
        uid = "1710e580-dfce-11ef-a98f-52b437312584"
        history_interface.WriteHistory(uid, uid, "test", "test")

    assert (
        "Wrote a new entry to the user history for user." in caplog.records[-1].message
    )
