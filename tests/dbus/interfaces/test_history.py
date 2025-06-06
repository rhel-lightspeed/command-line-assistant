from unittest.mock import patch

import pytest
from dasbus.server.template import InterfaceTemplate

from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.repository.chat import ChatRepository
from command_line_assistant.dbus.exceptions import (
    HistoryNotAvailableError,
    HistoryNotEnabledError,
)
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


@pytest.fixture(autouse=True)
def _seed_test_database(universal_user_id, mock_config):
    chat_repository = ChatRepository(DatabaseManager(mock_config))
    chat_repository.insert(
        {"user_id": universal_user_id, "name": "test", "description": "test"}
    )


@pytest.fixture
def get_chat_id(mock_config):
    chat_repository = ChatRepository(DatabaseManager(mock_config))
    result = chat_repository.select_first()

    return result[0].id


def test_history_interface_get_history(
    history_interface, mock_history_entry, universal_user_id, get_chat_id
):
    """Test getting all history through history interface."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write(
            get_chat_id,
            universal_user_id,
            "test query",
            "test response",
        )
        response = history_interface.GetHistory(universal_user_id)

        reconstructed = HistoryList.from_structure(response)
        assert len(reconstructed.histories) == 1
        assert reconstructed.histories[0].question == "test query"
        assert reconstructed.histories[0].response == "test response"


@pytest.mark.parametrize(
    ("exception", "match", "history_enabled"),
    (
        (
            HistoryNotAvailableError,
            "Looks like no history was found. Try asking something first!",
            True,
        ),
        (
            HistoryNotEnabledError,
            "Looks like history is not enabled yet. Enable it in the configuration file before trying to access history.",
            False,
        ),
    ),
)
def test_history_interface_get_history_multiple_exceptions(
    history_interface, exception, match, history_enabled
):
    """Test getting all history through history interface."""
    uid = "1710e580-dfce-11ef-a98f-52b437312584"
    history_interface.implementation.config.history.enabled = history_enabled
    with pytest.raises(
        exception,
        match=match,
    ):
        history_interface.GetHistory(uid)


def test_history_interface_get_first_conversation(
    history_interface, mock_history_entry, universal_user_id, get_chat_id
):
    """Test getting first conversation through history interface."""

    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write(get_chat_id, universal_user_id, "test query", "test response")
        manager.write(get_chat_id, universal_user_id, "test query2", "test response2")
        manager.write(get_chat_id, universal_user_id, "test query3", "test response3")
        response = history_interface.GetFirstConversation(universal_user_id, "test")

        reconstructed = HistoryList.from_structure(response)
        assert len(reconstructed.histories) == 1
        assert reconstructed.histories[0].question == "test query"
        assert reconstructed.histories[0].response == "test response"


@pytest.mark.parametrize(
    ("exception", "match", "history_enabled"),
    (
        (
            HistoryNotAvailableError,
            "Looks like no history was found. Try asking something first!",
            True,
        ),
        (
            HistoryNotEnabledError,
            "Looks like history is not enabled yet. Enable it in the configuration file before trying to access history.",
            False,
        ),
    ),
)
def test_history_interface_get_first_conversation_multiple_exception(
    history_interface, _seed_test_database, exception, match, history_enabled
):
    uid = "1710e580-dfce-11ef-a98f-52b437312584"
    history_interface.implementation.config.history.enabled = history_enabled
    with pytest.raises(
        exception,
        match=match,
    ):
        history_interface.GetFirstConversation(uid, "test")


def test_history_interface_get_last_conversation(
    history_interface, mock_history_entry, universal_user_id, get_chat_id
):
    """Test getting first conversation through history interface."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write(get_chat_id, universal_user_id, "test query", "test response")
        manager.write(get_chat_id, universal_user_id, "test query2", "test response2")
        manager.write(get_chat_id, universal_user_id, "test query3", "test response3")
        response = history_interface.GetLastConversation(universal_user_id, "test")

        reconstructed = HistoryList.from_structure(response)
        assert len(reconstructed.histories) == 1
        assert reconstructed.histories[0].question == "test query3"
        assert reconstructed.histories[0].response == "test response3"


@pytest.mark.parametrize(
    ("exception", "match", "history_enabled"),
    (
        (
            HistoryNotAvailableError,
            "Looks like no history was found. Try asking something first!",
            True,
        ),
        (
            HistoryNotEnabledError,
            "Looks like history is not enabled yet. Enable it in the configuration file before trying to access history.",
            False,
        ),
    ),
)
def test_history_interface_get_last_conversation_multiple_exception(
    history_interface, exception, match, history_enabled
):
    uid = "1710e580-dfce-11ef-a98f-52b437312584"
    history_interface.implementation.config.history.enabled = history_enabled
    with pytest.raises(
        exception,
        match=match,
    ):
        history_interface.GetLastConversation(uid, "test")


def test_history_interface_get_filtered_conversation(
    history_interface, mock_history_entry, universal_user_id, get_chat_id
):
    """Test getting filtered conversation through history interface."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write(get_chat_id, universal_user_id, "test query", "test response")
        manager.write(get_chat_id, universal_user_id, "not a query", "not a response")
        response = history_interface.GetFilteredConversation(
            universal_user_id, filter="test", from_chat="test"
        )

        reconstructed = HistoryList.from_structure(response)
        assert len(reconstructed.histories) == 1
        assert reconstructed.histories[0].question == "test query"
        assert reconstructed.histories[0].response == "test response"


@pytest.mark.parametrize(
    ("exception", "match", "history_enabled"),
    (
        (
            HistoryNotAvailableError,
            "Looks like no history was found. Try asking something first!",
            True,
        ),
        (
            HistoryNotEnabledError,
            "Looks like history is not enabled yet. Enable it in the configuration file before trying to access history.",
            False,
        ),
    ),
)
def test_history_interface_get_filtered_conversation_multiple_exception(
    history_interface, exception, match, history_enabled
):
    uid = "1710e580-dfce-11ef-a98f-52b437312584"
    history_interface.implementation.config.history.enabled = history_enabled
    with pytest.raises(
        exception,
        match=match,
    ):
        history_interface.GetFilteredConversation(uid, filter="test", from_chat="test")


def test_history_interface_get_filtered_conversation_duplicate_entries_not_matching(
    history_interface, mock_history_entry, universal_user_id, get_chat_id
):
    """Test getting filtered conversation through duplicated history interface.

    This test will have a duplicated entry, but not matching the "id". This
    should be enough to be considered a new entry
    """
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write(get_chat_id, universal_user_id, "test query", "test response")
        manager.write(get_chat_id, universal_user_id, "test query", "test response")
        response = history_interface.GetFilteredConversation(
            universal_user_id, filter="test", from_chat="test"
        )

        reconstructed = HistoryList.from_structure(response)
        assert len(reconstructed.histories) == 2
        assert reconstructed.histories[0].question == "test query"
        assert reconstructed.histories[0].response == "test response"


def test_history_interface_clear_history(history_interface, caplog):
    """Test clearing history through history interface."""
    with patch("command_line_assistant.dbus.interfaces.history.HistoryManager"):
        uid = "1710e580-dfce-11ef-a98f-52b437312584"
        history_interface.ClearHistory(uid, from_chat="test")
        assert "Clearing history entries for user." in caplog.records[0].message


def test_history_interface_empty_history(
    mock_history_entry, history_interface, universal_user_id, get_chat_id
):
    """Test handling empty history in all methods."""
    with patch(
        "command_line_assistant.history.manager.HistoryManager", mock_history_entry
    ) as manager:
        manager.write(get_chat_id, universal_user_id, "test query", "test response")
        # Test all methods with empty history
        for method in [
            history_interface.GetFirstConversation,
            history_interface.GetLastConversation,
        ]:
            response = method(universal_user_id, from_chat="test")
            reconstructed = HistoryList.from_structure(response)
            assert len(reconstructed.histories) == 1


def test_write_history(history_interface, caplog):
    with patch("command_line_assistant.dbus.interfaces.history.HistoryManager"):
        uid = "1710e580-dfce-11ef-a98f-52b437312584"
        history_interface.WriteHistory(uid, uid, "test", "test")

    assert (
        "Wrote a new entry to the user history for user." in caplog.records[-1].message
    )
