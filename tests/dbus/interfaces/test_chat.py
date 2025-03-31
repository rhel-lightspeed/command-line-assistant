from unittest.mock import patch

import pytest
from dasbus.server.template import InterfaceTemplate

from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.repository.chat import ChatRepository
from command_line_assistant.dbus.exceptions import ChatNotFoundError
from command_line_assistant.dbus.interfaces.chat import (
    ChatInterface,
)
from command_line_assistant.dbus.structures.chat import (
    AttachmentInput,
    ChatList,
    Question,
    Response,
    StdinInput,
)


@pytest.fixture
def chat_interface(mock_context):
    """Create a QueryInterface instance with mock implementation."""
    interface = ChatInterface(mock_context)
    assert isinstance(interface, InterfaceTemplate)
    return interface


@pytest.fixture
def mock_repository(mock_config):
    return ChatRepository(DatabaseManager(mock_config))


def test_chat_interface_ask_question(chat_interface, mock_config):
    """Test retrieving answer from query interface."""
    expected_response = "test response"
    with patch(
        "command_line_assistant.dbus.interfaces.chat.submit",
        return_value=expected_response,
    ) as mock_submit:
        uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
        message_input = Question("test", StdinInput(), AttachmentInput())
        response = chat_interface.AskQuestion(uid, message_input.structure())

        mock_submit.assert_called_once_with(
            {
                "question": "test",
                "context": {
                    "stdin": "",
                    "attachments": {"contents": "", "mimetype": ""},
                },
            },
            mock_config,
        )

        reconstructed = Response.from_structure(response)
        assert reconstructed.message == expected_response


def test_get_all_chat_from_user(chat_interface, mock_repository):
    uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
    mock_repository.insert({"name": "test", "description": "test", "user_id": uid})
    response = chat_interface.GetAllChatFromUser(uid)

    result = ChatList.from_structure(response)
    assert result.chats[0].name == "test"


def test_delete_all_chat_for_user(chat_interface, mock_repository, caplog):
    uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
    mock_repository.insert({"name": "test", "description": "test", "user_id": uid})
    chat_interface.DeleteAllChatForUser(uid)

    assert "Deleting chat for user." in caplog.records[-1].message


def test_delete_all_chat_for_user_no_chat(chat_interface):
    uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
    with pytest.raises(ChatNotFoundError, match="No chat found to delete."):
        chat_interface.DeleteAllChatForUser(uid)


def test_delete_chat_for_user(chat_interface, mock_repository, caplog):
    uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
    mock_repository.insert({"name": "test", "description": "test", "user_id": uid})
    chat_interface.DeleteChatForUser(uid, "test")

    assert "Deleting the request chat for user." in caplog.records[-1].message


def test_delete_chat_for_user_exception(chat_interface):
    uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
    with pytest.raises(
        ChatNotFoundError,
        match="Couldn't find chat with name 'test'. Check the name requested and try again.",
    ):
        chat_interface.DeleteChatForUser(uid, "test")


def test_get_latest_chat_from_user(chat_interface, mock_repository):
    uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
    inserted = mock_repository.insert(
        {"name": "test", "description": "test", "user_id": uid}
    )
    result = chat_interface.GetLatestChatFromUser(uid)
    assert result == str(inserted[0])


def test_get_chat_id(chat_interface, mock_repository, caplog):
    uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
    inserted = mock_repository.insert(
        {"name": "test", "description": "test", "user_id": uid}
    )
    result = chat_interface.GetChatId(uid, "test")
    assert result == str(inserted[0])
    assert f"name 'test' for user '{uid}'" in caplog.records[-1].message


def test_get_chat_id_exception(chat_interface):
    uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
    with pytest.raises(
        ChatNotFoundError,
        match="No chat found with name 'test'. Please, make sure that this chat exist first.",
    ):
        chat_interface.GetChatId(uid, "test")


def test_create_chat(
    chat_interface,
):
    uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
    result = chat_interface.CreateChat(uid, "test", "test")
    assert result
    assert "-" in result


@pytest.mark.parametrize(
    ("available", "name", "expected"), ((True, "test", True), (False, "test", False))
)
def test_is_chat_available(
    chat_interface, mock_repository, caplog, available, name, expected
):
    uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
    chat_interface.IsChatAvailable(uid, name)
    if available:
        mock_repository.insert({"name": name, "description": "test", "user_id": uid})

    result = chat_interface.IsChatAvailable(uid, name)
    assert result == expected
    if available:
        assert (
            f"Chat session with name '{name}' found for user '{uid}'."
            in caplog.records[-1].message
        )
    else:
        assert (
            f"Chat session with name '{name}' not found for user '{uid}'."
            in caplog.records[-1].message
        )
