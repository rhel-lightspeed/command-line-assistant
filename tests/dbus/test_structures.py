from command_line_assistant.dbus.structures import HistoryEntry, HistoryItem, Message


def test_message_init():
    message = Message()
    assert message.message == ""


def test_message_setter():
    message = Message()
    message.message = "test message"
    assert message.message == "test message"


def test_history_entry_init():
    history = HistoryEntry()
    assert history.entries == []


def test_history_entry_setter():
    history = HistoryEntry()
    test_entries = [HistoryItem(), HistoryItem(), HistoryItem()]
    history.entries = test_entries
    assert history.entries == test_entries


def test_history_entry_empty_list():
    history = HistoryEntry()
    history.entries = []
    assert history.entries == []


def test_message_empty_string():
    message = Message()
    message.message = ""
    assert message.message == ""


def test_history_entry_single_entry():
    history = HistoryEntry()

    history.entries = [HistoryItem()]
    assert len(history.entries) == 1
