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

    def read(self, user_id):
        self.read_called = True
        return []

    def write(self, user_id, query: str, response: str) -> None:
        self.write_called = True

    def clear(self, user_id) -> None:
        self.clear_called = True


@pytest.fixture
def history_manager(mock_config):
    return HistoryManager(mock_config, 1000, plugin=LocalHistory)


def test_history_manager_initialization(mock_config):
    """Test that HistoryManager initializes correctly"""
    manager = HistoryManager(mock_config, 1000)
    assert manager._config == mock_config
    assert manager._plugin is None
    assert manager._instance is None


def test_history_manager_plugin_setter(mock_config):
    """Test setting a valid plugin"""
    manager = HistoryManager(mock_config, 1000)
    manager.plugin = MockHistoryPlugin
    assert manager._plugin == MockHistoryPlugin
    assert isinstance(manager._instance, MockHistoryPlugin)


def test_history_manager_invalid_plugin(mock_config):
    """Test setting an invalid plugin"""
    manager = HistoryManager(mock_config, 1000)

    class InvalidPlugin(BaseHistoryPlugin):
        pass

    with pytest.raises(TypeError):
        manager.plugin = InvalidPlugin


def test_history_manager_read_without_plugin(mock_config):
    """Test reading history without setting a plugin first"""
    manager = HistoryManager(mock_config, 1000)
    with pytest.raises(RuntimeError):
        manager.read()


def test_history_manager_write_without_plugin(mock_config):
    """Test writing history without setting a plugin first"""
    manager = HistoryManager(mock_config, 1000)
    with pytest.raises(RuntimeError):
        manager.write("test query", "test response")


def test_history_manager_clear_without_plugin(mock_config):
    """Test clearing history without setting a plugin first"""
    manager = HistoryManager(mock_config, 1000)
    with pytest.raises(RuntimeError):
        manager.clear()


def test_history_manager_read(history_manager):
    """Test reading history"""
    history = history_manager.read()
    assert isinstance(history, list)
    assert len(history) == 0
    assert isinstance(history_manager._instance, LocalHistory)


def test_history_manager_write(history_manager):
    """Test writing to history"""
    test_query = "How do I check disk space?"
    test_response = "Use the df command"

    history_manager.write(test_query, test_response)

    history = history_manager.read()
    assert len(history) == 1
    assert history[0]["query"] == test_query
    assert history[0]["response"] == test_response


def test_history_manager_clear(history_manager):
    """Test clearing history"""
    # First write something
    history_manager.write("test query", "test response")
    assert len(history_manager.read()) == 1

    # Then clear it
    history_manager.clear()
    assert len(history_manager.read()) == 0


def test_history_manager_multiple_writes(history_manager):
    """Test multiple writes to history"""
    entries = [
        ("query1", "response1"),
        ("query2", "response2"),
        ("query3", "response3"),
    ]

    for query, response in entries:
        history_manager.write(query, response)

    history = history_manager.read()
    assert len(history) == len(entries)

    for i, (query, response) in enumerate(entries):
        assert history[i]["query"] == query
        assert history[i]["response"] == response
