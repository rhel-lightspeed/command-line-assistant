import pytest

from command_line_assistant.history.base import BaseHistoryPlugin
from command_line_assistant.history.manager import HistoryManager
from command_line_assistant.history.plugins.local import LocalHistory


class MockHistoryPlugin(BaseHistoryPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.read_called = False
        self.write_called = False
        self.clear_called = False
        self.clear_from_chat_called = True

    def read(self, user_id):
        self.read_called = True
        return []

    def read_from_chat(self, user_id: str, from_chat: str):
        return None

    def write(self, chat_id, user_id, query: str, response: str) -> None:
        self.write_called = True

    def clear(self, user_id) -> None:
        self.clear_called = True

    def clear_from_chat(self, user_id, from_chat):
        self._clear_from_chat_called = True


@pytest.fixture
def history_manager(mock_config):
    return HistoryManager(mock_config, plugin=LocalHistory)


def test_history_manager_initialization(mock_config):
    """Test that HistoryManager initializes correctly"""
    manager = HistoryManager(mock_config)
    assert manager._config == mock_config
    assert manager._plugin is None
    assert manager._instance is None


def test_history_manager_plugin_setter(mock_config):
    """Test setting a valid plugin"""
    manager = HistoryManager(mock_config)
    manager.plugin = MockHistoryPlugin
    assert manager._plugin == MockHistoryPlugin
    assert isinstance(manager._instance, MockHistoryPlugin)


def test_history_manager_invalid_plugin(mock_config):
    """Test setting an invalid plugin"""
    manager = HistoryManager(mock_config)

    class InvalidPlugin(BaseHistoryPlugin):
        pass

    with pytest.raises(TypeError):
        manager.plugin = InvalidPlugin


def test_history_manager_read_without_plugin(mock_config):
    """Test reading history without setting a plugin first"""
    manager = HistoryManager(mock_config)
    with pytest.raises(RuntimeError):
        manager.read("6d4e6b1e-dfcb-11ef-9b4f-52b437312584")


def test_history_manager_write_without_plugin(mock_config):
    """Test writing history without setting a plugin first"""
    manager = HistoryManager(mock_config)
    with pytest.raises(RuntimeError):
        manager.write(
            "6d4e6b1e-dfcb-11ef-9b4f-52b437312584",
            "6d4e6b1e-dfcb-11ef-9b4f-52b437312584",
            "test query",
            "test response",
        )


def test_history_manager_clear_without_plugin(mock_config):
    """Test clearing history without setting a plugin first"""
    manager = HistoryManager(mock_config)
    with pytest.raises(RuntimeError):
        manager.clear("6d4e6b1e-dfcb-11ef-9b4f-52b437312584")


def test_history_manager_read(history_manager):
    """Test reading history"""
    history = history_manager.read("6d4e6b1e-dfcb-11ef-9b4f-52b437312584")
    assert isinstance(history, list)
    assert len(history) == 0
    assert isinstance(history_manager._instance, LocalHistory)


def test_history_manager_write(history_manager):
    """Test writing to history"""
    test_query = "How do I check disk space?"
    test_response = "Use the df command"
    uid = "6d4e6b1e-dfcb-11ef-9b4f-52b437312584"
    history_manager.write(uid, uid, test_query, test_response)

    history = history_manager.read(uid)
    assert len(history) == 1
    assert history[0].interactions[0].question == test_query
    assert history[0].interactions[0].response == test_response


def test_history_manager_clear(history_manager):
    """Test clearing history"""
    # First write something
    uid = "6d4e6b1e-dfcb-11ef-9b4f-52b437312584"
    history_manager.write(uid, uid, "test query", "test response")
    data = history_manager.read(uid)
    assert len(data) == 1

    # Then clear it
    history_manager.clear(uid)
    assert len(history_manager.read(uid)) == 0


def test_history_manager_multiple_writes(history_manager):
    """Test multiple writes to history"""
    entries = [
        ("query1", "response1"),
        ("query2", "response2"),
        ("query3", "response3"),
    ]
    uid = "6d4e6b1e-dfcb-11ef-9b4f-52b437312584"
    for query, response in entries:
        history_manager.write(
            uid,
            uid,
            query,
            response,
        )

    history = history_manager.read(uid)
    # 1 history, with multiple interactions
    assert len(history) == 1
    assert len(history[0].interactions) == len(entries)
