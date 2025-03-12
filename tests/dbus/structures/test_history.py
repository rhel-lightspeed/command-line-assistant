import pytest

from command_line_assistant.dbus.structures.history import HistoryEntry, HistoryList


def test_history_entry_init():
    history = HistoryEntry()
    assert history.question == ""
    assert history.response == ""
    assert history.created_at == ""


@pytest.mark.parametrize(
    ("question", "response", "chat_name", "created_at"),
    (
        ("question", "response", "test", ""),
        ("", "response", "test", "2025-01-31 09:10:22.991148"),
        ("", "response", "", "2025-01-31 09:10:22.991148"),
        ("", "", "", ""),
        ("", "", "test", ""),
    ),
)
def test_history_entry_setter(question, response, chat_name, created_at):
    history = HistoryEntry(question, response, chat_name, created_at)
    assert history.question == question
    assert history.response == response
    assert history.chat_name == chat_name
    assert history.created_at == created_at


def test_history_list_empty_list():
    history = HistoryList()
    assert history.histories == []


def test_history_list_single_entry():
    history = HistoryList([HistoryEntry("test", "test", "2025-01-31 09:10:22.991148")])
    assert len(history.histories) == 1
