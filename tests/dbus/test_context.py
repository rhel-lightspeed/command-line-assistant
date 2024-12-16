import pytest

from command_line_assistant.dbus.context import (
    BaseContext,
    HistoryContext,
    QueryContext,
)
from command_line_assistant.dbus.structures import Message


@pytest.fixture
def base_context(mock_config):
    return BaseContext(mock_config)


@pytest.fixture
def query_context(mock_config):
    return QueryContext(mock_config)


@pytest.fixture
def history_context(mock_config):
    return HistoryContext(mock_config)


def test_base_context_config_property(mock_config):
    context = BaseContext(mock_config)
    assert context.config == mock_config


def test_query_context_initial_state(query_context):
    assert query_context.query is None
    assert query_context.query_changed is not None


def test_query_context_process_query(query_context):
    message_obj = Message()
    message_obj.message = "test query"
    signal_emitted = False

    def on_signal():
        nonlocal signal_emitted
        signal_emitted = True

    query_context.query_changed.connect(on_signal)
    query_context.process_query(message_obj)

    assert query_context.query == message_obj
    assert signal_emitted is True


def test_history_context_inheritance(history_context, mock_config):
    assert isinstance(history_context, BaseContext)
    assert history_context.config == mock_config
