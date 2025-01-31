from unittest.mock import patch

import pytest
from dasbus.server.template import InterfaceTemplate

from command_line_assistant.dbus.interfaces.chat import (
    ChatInterface,
)
from command_line_assistant.dbus.structures.chat import (
    AttachmentInput,
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


def test_chat_interface_ask_question(chat_interface, mock_config):
    """Test retrieving answer from query interface."""
    expected_response = "test response"
    with patch(
        "command_line_assistant.dbus.interfaces.chat.submit",
        return_value=expected_response,
    ) as mock_submit:
        uid = "2345f9e6-dfea-11ef-9ae9-52b437312584"
        message_input = Question("test", StdinInput(), AttachmentInput())
        response = chat_interface.AskQuestion(uid, uid, message_input.structure())

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
