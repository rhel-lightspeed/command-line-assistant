import pytest

from command_line_assistant.dbus.structures.chat import (
    AttachmentInput,
    ChatEntry,
    ChatList,
    StdinInput,
)


def test_initialize_chat_entry_default():
    chat = ChatEntry()
    assert chat.id == ""
    assert chat.name == ""
    assert chat.description == ""
    assert chat.created_at == ""
    assert chat.updated_at == ""
    assert chat.deleted_at == ""


@pytest.mark.parametrize(
    ("id", "name", "description", "created_at", "updated_at", "deleted_at"),
    (
        (
            "e101816c-dfcc-11ef-aab3-52b437312584",
            "test",
            "test",
            "2025-01-31 09:14:38.053427",
            "",
            "",
        ),
    ),
)
def test_initialize_chat_entry(
    id, name, description, created_at, updated_at, deleted_at
):
    chat = ChatEntry(id, name, description, created_at, updated_at, deleted_at)
    assert chat.id == id
    assert chat.name == name
    assert chat.description == description
    assert chat.created_at == created_at
    assert chat.updated_at == updated_at
    assert chat.deleted_at == deleted_at


def test_chat_list_initialize_default():
    chat = ChatList()

    assert chat.chats == []


def test_chat_list_initialize_single_entry():
    chat = ChatList(chats=[ChatEntry()])
    assert chat.chats
    assert len(chat.chats) == 1


def test_initialize_attachment_input_default():
    chat = AttachmentInput()
    assert chat.contents == ""
    assert chat.mimetype == ""


@pytest.mark.parametrize(("contents", "mimetype"), (("tests", "test/test"),))
def test_initialize_attachment_input(contents, mimetype):
    chat = AttachmentInput(contents, mimetype)
    assert chat.contents == contents
    assert chat.mimetype == mimetype


def test_initialize_stdin_input_default():
    chat = StdinInput()
    assert chat.stdin == ""


def test_initialize_stdin_input():
    chat = StdinInput("test")
    assert chat.stdin == "test"
