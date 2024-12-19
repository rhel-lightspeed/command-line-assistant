import pytest

from command_line_assistant.config import Config
from command_line_assistant.config.schemas import HistorySchema
from command_line_assistant.history.base import BaseHistory
from command_line_assistant.history.manager import HistoryManager
from command_line_assistant.history.schemas import (
    History,
    HistoryEntry,
    InteractionData,
    QueryData,
    ResponseData,
)


class MockHistoryPlugin(BaseHistory):
    def __init__(self, config):
        super().__init__(config)
        self.read_called = False
        self.write_called = False
        self.clear_called = False
        self._history = History()

    def read(self) -> History:
        self.read_called = True
        return self._history

    def write(self, current_history: History, query: str, response: str) -> None:
        self.write_called = True
        entry = HistoryEntry(
            interaction=InteractionData(
                query=QueryData(text=query), response=ResponseData(text=response)
            )
        )
        self._history.history.append(entry)

    def clear(self) -> None:
        self.clear_called = True
        self._history.history = []


@pytest.fixture
def mock_config(tmp_path):
    return Config(
        history=HistorySchema(enabled=True, file=tmp_path / "test_history.json")
    )


@pytest.fixture
def history_manager(mock_config):
    return HistoryManager(mock_config, plugin=MockHistoryPlugin)


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

    class InvalidPlugin(BaseHistory):
        pass

    with pytest.raises(TypeError):
        manager.plugin = InvalidPlugin


def test_history_manager_read_without_plugin(mock_config):
    """Test reading history without setting a plugin first"""
    manager = HistoryManager(mock_config)
    with pytest.raises(RuntimeError):
        manager.read()


def test_history_manager_write_without_plugin(mock_config):
    """Test writing history without setting a plugin first"""
    manager = HistoryManager(mock_config)
    with pytest.raises(RuntimeError):
        manager.write(History(), "test query", "test response")


def test_history_manager_clear_without_plugin(mock_config):
    """Test clearing history without setting a plugin first"""
    manager = HistoryManager(mock_config)
    with pytest.raises(RuntimeError):
        manager.clear()


def test_history_manager_read(history_manager):
    """Test reading history"""
    history = history_manager.read()
    assert isinstance(history, History)
    assert isinstance(history_manager._instance, MockHistoryPlugin)
    assert history_manager._instance.read_called


def test_history_manager_write(history_manager):
    """Test writing to history"""
    test_query = "How do I check disk space?"
    test_response = "Use the df command"

    history_manager.write(History(), test_query, test_response)

    assert history_manager._instance.write_called
    history = history_manager.read()
    assert len(history.history) == 1
    assert history.history[0].interaction.query.text == test_query
    assert history.history[0].interaction.response.text == test_response


def test_history_manager_clear(history_manager):
    """Test clearing history"""
    # First write something
    history_manager.write(History(), "test query", "test response")
    assert len(history_manager.read().history) == 1

    # Then clear it
    history_manager.clear()
    assert history_manager._instance.clear_called
    assert len(history_manager.read().history) == 0


def test_history_manager_multiple_writes(history_manager):
    """Test multiple writes to history"""
    entries = [
        ("query1", "response1"),
        ("query2", "response2"),
        ("query3", "response3"),
    ]

    for query, response in entries:
        history_manager.write(History(), query, response)

    history = history_manager.read()
    assert len(history.history) == len(entries)

    for i, (query, response) in enumerate(entries):
        assert history.history[i].interaction.query.text == query
        assert history.history[i].interaction.response.text == response
