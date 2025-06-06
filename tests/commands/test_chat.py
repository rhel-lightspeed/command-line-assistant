from argparse import Namespace
from datetime import datetime
from unittest.mock import patch

import pytest

from command_line_assistant.commands.chat import (
    ALWAYS_LEGAL_MESSAGE,
    LEGAL_NOTICE,
    InputSource,
    _create_chat_session,
    _display_response,
    _parse_attachment_file,
    _read_last_terminal_output,
    _submit_question,
    chat_command,
)
from command_line_assistant.dbus.exceptions import (
    ChatNotFoundError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.structures.chat import (
    ChatEntry,
    ChatList,
    Question,
    Response,
)
from command_line_assistant.exceptions import StopInteractiveMode
from command_line_assistant.utils.cli import CommandContext
from command_line_assistant.utils.files import NamedFileLock


@pytest.fixture
def default_namespace():
    return Namespace(
        query_string="",
        stdin="",
        attachment=None,
        interactive=False,
        list=False,
        delete="",
        delete_all=False,
        name="",
        description="",
        with_output=None,
        plain=True,
    )


@pytest.fixture
def command_context():
    return CommandContext()


def test_chat_command_single_question(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test chat command with a single question."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("No chat found")
    mock_dbus_service.CreateChat.return_value = "test-chat"
    mock_dbus_service.AskQuestion.return_value = Response("Test response").structure()

    default_namespace.query_string = "test question"
    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Test response" in captured.out
    assert LEGAL_NOTICE in captured.out
    assert ALWAYS_LEGAL_MESSAGE in captured.out


def test_chat_command_list_chats(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test listing all chats."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetAllChatFromUser.return_value = ChatList(
        [
            ChatEntry(
                name="test-chat",
                description="Test description",
                created_at=str(datetime.now()),
            )
        ]
    ).structure()

    default_namespace.list = True
    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Found a total of 1 chats:" in captured.out
    assert "test-chat" in captured.out


def test_chat_command_list_no_chats(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test listing when no chats exist."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetAllChatFromUser.return_value = ChatList([]).structure()

    default_namespace.list = True
    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "No chats available." in captured.out


def test_chat_command_delete_chat(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test deleting a specific chat."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.DeleteChatForUser.return_value = None

    default_namespace.delete = "test-chat"
    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Chat test-chat deleted successfully." in captured.out


def test_chat_command_delete_chat_not_found(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test deleting a chat that doesn't exist."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.DeleteChatForUser.side_effect = ChatNotFoundError(
        "Chat not found"
    )

    default_namespace.delete = "nonexistent-chat"
    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 80  # ChatCommandException code
    assert "Failed to delete requested chat" in captured.err


def test_chat_command_delete_all_chats(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test deleting all chats."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.DeleteAllChatForUser.return_value = None

    default_namespace.delete_all = True
    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Deleted all chats successfully." in captured.out


def test_chat_command_interactive_mode(
    mock_dbus_service, default_namespace, command_context
):
    """Test interactive mode."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("No chat found")
    mock_dbus_service.CreateChat.return_value = "test-chat"
    mock_dbus_service.AskQuestion.return_value = Response("Test response").structure()

    default_namespace.interactive = True

    with patch(
        "command_line_assistant.commands.chat.create_interactive_renderer"
    ) as mock_renderer:
        mock_renderer.return_value.render.side_effect = [None, StopInteractiveMode()]
        mock_renderer.return_value.output = "test question"

        result = chat_command(default_namespace, command_context)
        assert result == 0


def test_chat_command_interactive_with_terminal_capture(
    default_namespace, command_context, capsys
):
    """Test interactive mode fails when terminal capture is active."""
    default_namespace.interactive = True

    with NamedFileLock(name="terminal"):
        result = chat_command(default_namespace, command_context)
        captured = capsys.readouterr()
        assert result == 80  # Should fail with ChatCommandException
        assert "Detected a terminal capture session running" in captured.err


@pytest.mark.parametrize(
    ("query_string", "expected_error"),
    [
        ("", "Your query needs to have at least 2 characters"),
        ("a", "Your query needs to have at least 2 characters"),
    ],
)
def test_chat_command_validation_errors(
    query_string, expected_error, default_namespace, command_context, capsys
):
    """Test query validation errors."""
    default_namespace.query_string = query_string
    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 80
    assert expected_error in captured.err


def test_chat_command_stdin_validation(default_namespace, command_context, capsys):
    """Test stdin validation."""
    default_namespace.stdin = "a"  # Too short
    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 80
    assert "Your stdin input needs to have at least 2 characters." in captured.err


def test_chat_command_with_terminal_output(
    mock_dbus_service, default_namespace, command_context, tmp_path, capsys
):
    """Test using terminal output without capture active."""
    default_namespace.query_string = "test question"
    default_namespace.with_output = 1

    # Mock terminal capture file not existing
    with patch(
        "command_line_assistant.commands.chat.TERMINAL_CAPTURE_FILE"
    ) as mock_file:
        mock_file.exists.return_value = False
        result = chat_command(default_namespace, command_context)
        captured = capsys.readouterr()
        assert result == 80  # Should fail
        assert "Adding context from terminal output is only allowed" in captured.err


def test_chat_command_name_and_description_defaults(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test default name and description handling."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("No chat found")
    mock_dbus_service.CreateChat.return_value = "test-chat"
    mock_dbus_service.AskQuestion.return_value = Response("Test response").structure()

    default_namespace.query_string = "test question"
    # No name or description provided
    result = chat_command(default_namespace, command_context)

    assert result == 0
    # Should use defaults without warnings since both are empty


def test_chat_command_name_without_description(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test providing name without description."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("No chat found")
    mock_dbus_service.CreateChat.return_value = "test-chat"
    mock_dbus_service.AskQuestion.return_value = Response("Test response").structure()

    default_namespace.query_string = "test question"
    default_namespace.name = "custom-chat"
    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Chat description not provided" in captured.err


def test_chat_command_description_without_name(
    mock_dbus_service, default_namespace, command_context, capsys
):
    """Test providing description without name."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("No chat found")
    mock_dbus_service.CreateChat.return_value = "test-chat"
    mock_dbus_service.AskQuestion.return_value = Response("Test response").structure()

    default_namespace.query_string = "test question"
    default_namespace.description = "custom description"
    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Chat name not provided" in captured.err


@pytest.mark.parametrize(
    ("query_string", "stdin", "attachment", "last_output", "expected"),
    [
        ("test query", None, None, "", "test query"),
        (None, "stdin", None, "", "stdin"),
        ("query", "stdin", None, "", "query stdin"),
        (None, None, "file query", "", "file query"),
        ("query", None, "file query", "", "query file query"),
        (None, "stdin", "file query", "", "stdin file query"),
        (None, None, None, "last output", "last output"),
        ("query", None, "attachment", "last output", "query attachment last output"),
    ],
)
def test_input_source_get_input_source(
    query_string, stdin, attachment, last_output, expected
):
    """Test InputSource.get_input_source method."""
    input_source = InputSource(
        question=query_string or "",
        stdin=stdin or "",
        attachment=attachment or "",
        attachment_mimetype="",
        terminal_output=last_output or "",
    )
    result = input_source.get_input_source()
    assert result == expected


def test_input_source_no_input():
    """Test InputSource.get_input_source with no input."""
    input_source = InputSource("", "", "", "", "")
    with pytest.raises(
        ValueError,
        match="No input provided. Please provide input via file, stdin, or direct query.",
    ):
        input_source.get_input_source()


def test_parse_attachment_file_success(tmp_path):
    """Test parsing attachment file successfully."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test content")

    with open(file_path, "r") as f:
        result = _parse_attachment_file(f)

    assert result == "test content"


def test_parse_attachment_file_none():
    """Test parsing None attachment."""
    result = _parse_attachment_file(None)
    assert result == ""


def test_parse_attachment_file_unicode_error(tmp_path):
    """Test parsing binary file."""
    file_path = tmp_path / "test.bin"
    file_path.write_bytes(b"\x80\x81\x82")

    with pytest.raises(
        ValueError,
        match="File appears to be binary or contains invalid text encoding",
    ):
        with open(file_path, "r") as f:
            _parse_attachment_file(f)


def test_read_last_terminal_output():
    """Test reading last terminal output."""
    with (
        patch(
            "command_line_assistant.commands.chat.parse_terminal_output"
        ) as mock_parse,
        patch("command_line_assistant.commands.chat.find_output_by_index") as mock_find,
    ):
        mock_parse.return_value = [{"output": "test"}]
        mock_find.return_value = "test output"

        result = _read_last_terminal_output(-1)
        assert result == "test output"


def test_read_last_terminal_output_no_contents():
    """Test reading terminal output when no contents exist."""
    with patch(
        "command_line_assistant.commands.chat.parse_terminal_output"
    ) as mock_parse:
        mock_parse.return_value = []

        result = _read_last_terminal_output(-1)
        assert result == ""


def test_display_response(capsys):
    """Test display response function."""
    _display_response("test response", plain=True)

    captured = capsys.readouterr()
    assert LEGAL_NOTICE in captured.out
    assert "test response" in captured.out
    assert ALWAYS_LEGAL_MESSAGE in captured.out


def test_display_response_plain(capsys):
    """Test display response function in plain mode."""
    _display_response("test response", plain=True)

    captured = capsys.readouterr()
    assert LEGAL_NOTICE in captured.out
    assert "test response" in captured.out
    assert ALWAYS_LEGAL_MESSAGE in captured.out


def test_submit_question_success(mock_dbus_service):
    """Test submitting question successfully."""
    from command_line_assistant.utils.dbus import DbusUtils
    from command_line_assistant.utils.renderers import RenderUtils

    mock_dbus_service.AskQuestion.return_value = Response("test response").structure()
    mock_dbus_service.WriteHistory.return_value = None

    dbus = DbusUtils()
    render = RenderUtils(plain=True)

    # Create a proper Question object
    message_input = Question(
        message="test question",
        stdin=None,
        attachment=None,
        terminal=None,
        systeminfo=None,
    )

    result = _submit_question(
        dbus=dbus,
        user_id="test-user",
        chat_id="test-chat",
        message_input=message_input,
        plain=True,
    )

    assert result == "test response"


def test_submit_question_history_disabled(mock_dbus_service, caplog):
    """Test submitting question when history is disabled."""
    from command_line_assistant.utils.dbus import DbusUtils

    mock_dbus_service.AskQuestion.return_value = Response("test response").structure()
    mock_dbus_service.WriteHistory.side_effect = HistoryNotEnabledError(
        "History disabled"
    )

    dbus = DbusUtils()

    message_input = Question(
        message="test question",
        stdin=None,
        attachment=None,
        terminal=None,
        systeminfo=None,
    )

    result = _submit_question(
        dbus=dbus,
        user_id="test-user",
        chat_id="test-chat",
        message_input=message_input,
        plain=True,
    )

    assert result == "test response"
    assert "The history is disabled in the configuration file" in caplog.text


def test_create_chat_session_existing(mock_dbus_service):
    """Test creating chat session when one already exists."""
    from command_line_assistant.utils.dbus import DbusUtils

    mock_dbus_service.GetChatId.return_value = "existing-chat-id"

    dbus = DbusUtils()

    result = _create_chat_session(dbus, "test-user", "test-chat", "Test description")
    assert result == "existing-chat-id"


def test_create_chat_session_new(mock_dbus_service):
    """Test creating new chat session."""
    from command_line_assistant.utils.dbus import DbusUtils

    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("No chat found")
    mock_dbus_service.CreateChat.return_value = "new-chat-id"

    dbus = DbusUtils()

    result = _create_chat_session(dbus, "test-user", "test-chat", "Test description")
    assert result == "new-chat-id"


def test_chat_command_exception_handling(default_namespace, command_context, capsys):
    """Test that ChatCommandException is properly handled."""
    # Test with invalid query that should raise ChatCommandException
    default_namespace.query_string = ""  # Empty query
    default_namespace.stdin = ""  # Empty stdin

    result = chat_command(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 80  # ChatCommandException code
    assert "Your query needs to have at least 2 characters" in captured.err
