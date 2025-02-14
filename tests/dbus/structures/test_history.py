import pytest

from command_line_assistant.dbus.structures.history import HistoryEntry, HistoryList


def test_history_entry_init():
    history = HistoryEntry()
    assert history.question == ""
    assert history.response == ""
    assert history.created_at == ""


@pytest.mark.parametrize(
    ("question", "response", "created_at"),
    (
        ("question", "response", ""),
        ("", "response", "2025-01-31 09:10:22.991148"),
    ),
)
def test_history_entry_setter(question, response, created_at):
    history = HistoryEntry(question, response, created_at)
    assert history.question == question
    assert history.response == response
    assert history.created_at == created_at


def test_history_list_empty_list():
    history = HistoryList()
    assert history.histories == []


def test_history_list_single_entry():
    history = HistoryList([HistoryEntry("test", "test", "2025-01-31 09:10:22.991148")])
    assert len(history.histories) == 1
