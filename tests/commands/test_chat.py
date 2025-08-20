import os
from argparse import Namespace
from datetime import datetime
from unittest import mock
from unittest.mock import patch

import pytest

from command_line_assistant.commands import chat
from command_line_assistant.commands.chat import (
    _handle_legal_message,
)
from command_line_assistant.commands.cli import CommandContext
from command_line_assistant.dbus.client import DbusClient
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
from command_line_assistant.exceptions import ChatCommandException, StopInteractiveMode
from command_line_assistant.rendering.renderers import Renderer
from command_line_assistant.utils.files import NamedFileLock


@pytest.fixture
def default_namespace() -> Namespace:
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


@pytest.mark.parametrize(
    (
        "query_string",
        "stdin",
        "expected",
    ),
    (
        ("h", "", "Your query needs to have at least 2 characters."),
        ("", "h", "Your stdin input needs to have at least 2 characters."),
        ("h", "h", "Your query needs to have at least 2 characters."),
    ),
)
def test_chat_command_run_minimum_characters(
    query_string,
    stdin,
    expected,
    capsys,
    default_namespace,
    command_context,
):
    default_namespace.query_string = query_string
    default_namespace.stdin = stdin

    with pytest.raises(ChatCommandException, match=expected):
        chat._single_question(
            Renderer(plain=True),
            DbusClient(),
            command_context,
            default_namespace,
            "test-user",
            "test",
            "test",
        )


def test_single_question_invalid_query(default_namespace, command_context):
    default_namespace.query_string = "a"
    with pytest.raises(
        ChatCommandException, match="Your query needs to have at least 2 characters."
    ):
        chat._single_question(
            Renderer(plain=True),
            DbusClient(),
            command_context,
            default_namespace,
            "test-user",
            "test",
            "test",
        )


def test_single_question_value_error(default_namespace, command_context, monkeypatch):
    default_namespace.query_string = "ate"
    mock_func = mock.MagicMock()
    mock_func.side_effect = ValueError
    monkeypatch.setattr(chat, "_create_chat_session", mock_func)
    with pytest.raises(
        ChatCommandException, match="Failed to get a response from LLM.*"
    ):
        chat._single_question(
            Renderer(plain=True),
            DbusClient(),
            command_context,
            default_namespace,
            "test-user",
            "test",
            "test",
        )


def test_list_chats(mock_dbus_service, capsys):
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

    result = chat._list_chats(Renderer(plain=True), DbusClient(), user_id="test")

    captured = capsys.readouterr()
    assert result == 0
    assert "Found a total of 1 chats:" in captured.out
    assert "test-chat" in captured.out


def test_list_no_chats(mock_dbus_service, default_namespace, command_context, capsys):
    """Test listing when no chats exist."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetAllChatFromUser.return_value = ChatList([]).structure()

    default_namespace.list = True
    result = chat._list_chats(Renderer(True), DbusClient(), "test-user")

    captured = capsys.readouterr()
    assert result == 0
    assert "No chats available." in captured.out


def test_delete_chat(mock_dbus_service, capsys):
    """Test deleting a specific chat."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.DeleteChatForUser.return_value = None

    result = chat._delete_chat(Renderer(True), DbusClient(), "test", "test-chat")

    captured = capsys.readouterr()
    assert result == 0
    assert "Chat test-chat deleted successfully." in captured.out


def test_delete_chat_not_found(mock_dbus_service):
    """Test deleting a chat that doesn't exist."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.DeleteChatForUser.side_effect = ChatNotFoundError(
        "Chat not found"
    )
    with pytest.raises(ChatCommandException, match="Failed to delete requested chat"):
        chat._delete_chat(Renderer(True), DbusClient(), "test", "test")


def test_delete_all_chats(mock_dbus_service, capsys):
    """Test deleting all chats."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.DeleteAllChatForUser.return_value = None

    result = chat._delete_all_chats(Renderer(True), DbusClient(), "test-user")

    captured = capsys.readouterr()
    assert result == 0
    assert "Deleted all chats successfully." in captured.out


def test_delete_all_chats_exception(mock_dbus_service, capsys):
    """Test deleting all chats."""
    mock_dbus_service.DeleteAllChatForUser.side_effect = ChatNotFoundError(
        "chat not found"
    )

    with pytest.raises(
        ChatCommandException,
        match="Failed to delete all requested chats chat not found",
    ):
        chat._delete_all_chats(Renderer(True), DbusClient(), "test-user")


def test_interactive_mode(mock_dbus_service, default_namespace, command_context):
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

        result = chat._interactive_chat(
            Renderer(True),
            DbusClient(),
            command_context,
            default_namespace,
            "test-user",
            "test",
            "test",
        )
        assert result == 0


def test_interactive_mode_empty_question(default_namespace, command_context, capsys):
    """Test interactive mode with empty question"""
    with patch(
        "command_line_assistant.commands.chat.create_interactive_renderer"
    ) as mock_renderer:
        mock_renderer.return_value.render.side_effect = [None, StopInteractiveMode()]
        mock_renderer.return_value.output = ""

        chat._interactive_chat(
            Renderer(True),
            DbusClient(),
            command_context,
            default_namespace,
            "test-user",
            "test",
            "test",
        )

        captured = capsys.readouterr()
        assert "Your question can't be empty" in captured.err


def test_interactive_mode_keyboard_interrupt(default_namespace, command_context):
    """Test interactive mode with empty question"""
    with patch(
        "command_line_assistant.commands.chat.create_interactive_renderer"
    ) as mock_renderer:
        mock_renderer.return_value.render.side_effect = [KeyboardInterrupt]

        with pytest.raises(
            ChatCommandException,
            match="Detected keyboard interrupt. Stopping interactive mode.",
        ):
            chat._interactive_chat(
                Renderer(True),
                DbusClient(),
                command_context,
                default_namespace,
                "test-user",
                "test",
                "test",
            )


def test_interactive_with_terminal_capture(default_namespace, command_context, capsys):
    """Test interactive mode fails when terminal capture is active."""
    default_namespace.interactive = True

    with NamedFileLock(name="terminal"):
        with pytest.raises(
            ChatCommandException,
            match="Detected a terminal capture session running with pid.*",
        ):
            chat._interactive_chat(
                Renderer(True),
                DbusClient(),
                command_context,
                default_namespace,
                "test-user",
                "test",
                "test",
            )


@pytest.mark.parametrize(
    ("query_string", "expected_error"),
    [
        ("a", "Your query needs to have at least 2 characters"),
    ],
)
def test_validation_errors(query_string, expected_error, default_namespace):
    """Test query validation errors."""
    default_namespace.query_string = query_string
    result = chat._validate_query_composition(default_namespace)

    assert expected_error in result


def test_stdin_validation(default_namespace):
    """Test stdin validation."""
    default_namespace.stdin = "a"  # Too short
    result = chat._validate_query_composition(default_namespace)

    assert "Your stdin input needs to have at least 2 characters." == result


def test_with_terminal_output(default_namespace):
    """Test using terminal output without capture active."""
    default_namespace.query_string = "test question"
    default_namespace.with_output = 1

    # Mock terminal capture file not existing
    with patch(
        "command_line_assistant.commands.chat.TERMINAL_CAPTURE_FILE"
    ) as mock_file:
        mock_file.exists.return_value = False
        result = chat._validate_query_composition(default_namespace)
        assert (
            "Adding context from terminal output is only allowed if terminal capture is active."
            == result
        )


def test_chat_command_name_and_description_defaults(
    mock_dbus_service, default_namespace, command_context
):
    """Test default name and description handling."""
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("No chat found")
    mock_dbus_service.CreateChat.return_value = "test-chat"
    mock_dbus_service.AskQuestion.return_value = Response("Test response").structure()

    default_namespace.query_string = "test question"
    # No name or description provided
    result = chat.chat_command.func(default_namespace, command_context)

    assert result == 0


def test_chat_command_with_terminal_output(
    mock_dbus_service, default_namespace, command_context
):
    """Test parsing with_output in chat_command.

    This test will return 80 (error), but we don't care of the rest of the flow
    execution.
    """
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("No chat found")
    mock_dbus_service.CreateChat.return_value = "test-chat"
    mock_dbus_service.AskQuestion.return_value = Response("Test response").structure()

    default_namespace.query_string = "test question"
    default_namespace.with_output = -1
    # No name or description provided
    result = chat.chat_command.func(default_namespace, command_context)

    assert result == 80


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
    result = chat.chat_command.func(default_namespace, command_context)

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
    result = chat.chat_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Chat name not provided" in captured.err


def test_chat_command_exception(
    mock_dbus_service, default_namespace, command_context, capsys, monkeypatch
):
    mock_func = mock.MagicMock()
    mock_func.side_effect = ChatCommandException("failed")
    monkeypatch.setattr(chat, "_single_question", mock_func)
    default_namespace.query_string = "test question"
    result = chat.chat_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 80
    assert "failed" in captured.err


def test_parse_attachment_file_success(tmp_path):
    """Test parsing attachment file successfully."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test content")

    with open(file_path, "r") as f:
        result = chat._parse_attachment_file(f)

    assert result == "test content"


def test_parse_attachment_file_none():
    """Test parsing None attachment."""
    result = chat._parse_attachment_file(None)
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
            chat._parse_attachment_file(f)


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

        result = chat._read_last_terminal_output(-1)
        assert result == "test output"


def test_read_last_terminal_output_no_contents():
    """Test reading terminal output when no contents exist."""
    with patch(
        "command_line_assistant.commands.chat.parse_terminal_output"
    ) as mock_parse:
        mock_parse.return_value = []

        result = chat._read_last_terminal_output(-1)
        assert result == ""


@pytest.mark.parametrize(
    ("plain"),
    (
        (True),
        (False),
    ),
)
def test_display_response(plain, capsys, tmp_path, monkeypatch):
    """Test display response function."""
    monkeypatch.setattr(chat, "get_xdg_state_path", lambda: tmp_path)

    chat._display_response("test response", plain=plain)

    captured = capsys.readouterr()
    assert "This feature uses AI technology." in captured.out
    assert "test response" in captured.out
    assert "" in captured.out


def test_submit_question_success(mock_dbus_service):
    """Test submitting question successfully."""

    mock_dbus_service.AskQuestion.return_value = Response("test response").structure()
    mock_dbus_service.WriteHistory.return_value = None

    dbus = DbusClient()

    # Create a proper Question object
    message_input = Question(
        message="test question",
        stdin=None,
        attachment=None,
        terminal=None,
        systeminfo=None,
    )

    result = chat._submit_question(
        dbus=dbus,
        user_id="test-user",
        chat_id="test-chat",
        message_input=message_input,
        plain=True,
    )

    assert result == "test response"


def test_submit_question_history_disabled(mock_dbus_service, caplog):
    """Test submitting question when history is disabled."""

    mock_dbus_service.AskQuestion.return_value = Response("test response").structure()
    mock_dbus_service.WriteHistory.side_effect = HistoryNotEnabledError(
        "History disabled"
    )

    dbus = DbusClient()

    message_input = Question(
        message="test question",
        stdin=None,
        attachment=None,
        terminal=None,
        systeminfo=None,
    )

    result = chat._submit_question(
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

    mock_dbus_service.GetChatId.return_value = "existing-chat-id"

    dbus = DbusClient()

    result = chat._create_chat_session(
        dbus, "test-user", "test-chat", "Test description"
    )
    assert result == "existing-chat-id"


def test_create_chat_session_new(mock_dbus_service):
    """Test creating new chat session."""

    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("No chat found")
    mock_dbus_service.CreateChat.return_value = "new-chat-id"

    dbus = DbusClient()

    result = chat._create_chat_session(
        dbus, "test-user", "test-chat", "Test description"
    )
    assert result == "new-chat-id"


def test_trim_down_message_size(capsys, caplog):
    render = Renderer(plain=True)

    chat._trim_message_size(render, "test " * 6500)
    captured = capsys.readouterr()
    assert "The total size of your question and context" in captured.err
    assert "Final size of question after the limit" in caplog.records[-1].message


class TestInputSource:
    @pytest.mark.parametrize(
        ("query_string", "stdin", "attachment", "last_output", "expected"),
        [
            # query
            ("test query", None, None, "", "test query"),
            # stdin
            (None, "stdin", None, "", "stdin"),
            # query + stdin
            ("query", "stdin", None, "", "query stdin"),
            #  attachment
            (None, None, "file query", "", "file query"),
            #  query + attachment
            ("query", None, "file query", "", "query file query"),
            # stdin + attachment
            (None, "stdin", "file query", "", "stdin file query"),
            # Last output
            (None, None, None, "last output", "last output"),
            # Query + attachment + last output
            (
                "query",
                None,
                "attachment",
                "last output",
                "query attachment last output",
            ),
            # All input sources
            ("query", "stdin", "attachment", "last output", "query attachment"),
            # Query + last output
            ("query", None, None, "last output", "query last output"),
        ],
    )
    def test_input_source_get_input_source(
        self, query_string, stdin, attachment, last_output, expected
    ):
        """Test InputSource.get_input_source method."""
        input_source = chat.InputSource(
            question=query_string or "",
            stdin=stdin or "",
            attachment=attachment or "",
            attachment_mimetype="",
            terminal_output=last_output or "",
        )
        result = input_source.get_input_source()
        assert result == expected

    def test_input_source_no_input(self):
        """Test InputSource.get_input_source with no input."""
        input_source = chat.InputSource("", "", "", "", "")
        with pytest.raises(
            ValueError,
            match="No input provided. Please provide input via file, stdin, or direct query.",
        ):
            input_source.get_input_source()


def test_handle_legal_message_first_write(tmp_path, monkeypatch):
    """Test first write with decorator"""
    state_file = tmp_path / "legal"
    monkeypatch.setattr(chat, "get_xdg_state_path", lambda: tmp_path)
    result = _handle_legal_message()
    assert result
    assert state_file.exists()


def test_handle_legal_message_file_exists(tmp_path, monkeypatch):
    """Test subsequent writes with decorator"""
    parent_pid = str(os.getppid())
    state_file = tmp_path / "legal"
    state_file.write_text(parent_pid)
    monkeypatch.setattr(chat, "get_xdg_state_path", lambda: tmp_path)
    result = _handle_legal_message()

    assert not result
    assert state_file.read_text() == parent_pid


def test_state_file_and_folder_permissions(tmp_path, monkeypatch):
    """Test state file permissions"""
    state_file = tmp_path / "legal"
    monkeypatch.setattr(chat, "get_xdg_state_path", lambda: tmp_path)
    result = _handle_legal_message()

    assert result
    assert state_file.exists()
    assert oct(state_file.stat().st_mode)[-3:] == "600"
    assert oct(tmp_path.stat().st_mode)[-3:] == "700"


def test_different_pid(tmp_path, monkeypatch):
    state_file = tmp_path / "legal"
    state_file.write_text("1234")
    monkeypatch.setattr(chat, "get_xdg_state_path", lambda: tmp_path)
    result = _handle_legal_message()

    current_pid = str(os.getppid())
    assert result
    assert state_file.read_text() == current_pid


@pytest.mark.parametrize(
    ("arg", "mock_func", "mock_return"),
    (
        ("list", "_list_chats", lambda x, y, z: 0),
        ("delete", "_delete_chat", lambda x, y, z, a: 0),
        ("delete_all", "_delete_all_chats", lambda x, y, z: 0),
        ("interactive", "_interactive_chat", lambda x, y, z, a, b, c, d: 0),
        ("", "_single_question", lambda x, y, z, a, b, c, d: 0),
    ),
)
def test_chat_command(
    mock_dbus_service,
    default_namespace,
    command_context,
    monkeypatch,
    arg,
    mock_func,
    mock_return,
):
    monkeypatch.setattr(chat, mock_func, mock_return)
    default_namespace.query_string = "test"
    dict_args = vars(default_namespace)
    dict_args[arg] = True

    assert chat.chat_command.func(Namespace(**dict_args), command_context) == 0


def test_gather_input_sources(default_namespace, monkeypatch):
    default_namespace.with_output = True
    default_namespace.query_string = "test"
    monkeypatch.setattr(chat, "_read_last_terminal_output", lambda x: "test")
    monkeypatch.setattr(chat, "_parse_attachment_file", lambda x: "test")
    monkeypatch.setattr(chat, "guess_mimetype", lambda x: "test")

    result = chat._gather_input_sources(default_namespace)
    assert result.question == "test"
    assert result.attachment == "test"
    assert result.attachment_mimetype == "test"
    assert result.terminal_output == "test"
