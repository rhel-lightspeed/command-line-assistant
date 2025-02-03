from argparse import ArgumentParser, Namespace
from unittest import mock
from unittest.mock import patch

import pytest

from command_line_assistant.commands.chat import (
    ChatCommand,
    _command_factory,
    _parse_attachment_file,
    register_subcommand,
)
from command_line_assistant.dbus.exceptions import (
    ChatNotFoundError,
    CorruptedHistoryError,
    MissingHistoryFileError,
    RequestFailedError,
)
from command_line_assistant.dbus.structures.chat import ChatEntry, ChatList, Response


@pytest.fixture
def default_namespace():
    return Namespace(
        query_string=None,
        stdin=None,
        attachment=None,
        interactive=None,
        list=None,
        delete=None,
        delete_all=None,
        name=None,
        description=None,
    )


# Mock the entire DBus service/constants module
@pytest.fixture(autouse=True)
def mock_dbus_service(mock_proxy):
    """Fixture to mock DBus service and automatically use it for all tests"""
    with (
        patch("command_line_assistant.commands.chat.CHAT_IDENTIFIER") as mock_service,
        patch("command_line_assistant.commands.chat.HISTORY_IDENTIFIER"),
        patch("command_line_assistant.commands.chat.USER_IDENTIFIER"),
    ):
        # Create a mock proxy that will be returned by get_proxy()
        mock_service.get_proxy.return_value = mock_proxy

        # Setup default mock response
        mock_output = Response("default mock response")
        mock_proxy.RetrieveAnswer = lambda: mock_output.structure()

        yield mock_proxy


def test_query_command_initialization(default_namespace):
    """Test QueryCommand initialization"""
    default_namespace.query_string = "test query"
    command = ChatCommand(default_namespace)
    assert command._query == default_namespace.query_string


@pytest.mark.parametrize(
    (
        "test_input",
        "expected_output",
    ),
    [
        ("how to list files?", "Use the ls command"),
        ("what is linux?", "Linux is an operating system"),
        ("test!@#$%^&*()_+ query", "response with special chars !@#%"),
    ],
)
def test_query_command_run(
    mock_dbus_service, test_input, expected_output, capsys, default_namespace
):
    """Test QueryCommand run method with different inputs"""
    # Setup mock response for this specific test
    mock_output = Response(expected_output)
    mock_dbus_service.AskQuestion = lambda user_id, mock_input: mock_output.structure()
    default_namespace.query_string = test_input
    command = ChatCommand(default_namespace)
    command.run()

    # Verify output was printed
    captured = capsys.readouterr()
    assert expected_output in captured.out.strip()


def test_query_command_empty_response(mock_dbus_service, capsys, default_namespace):
    """Test QueryCommand handling empty response"""
    # Setup empty response
    mock_output = Response("")
    mock_dbus_service.AskQuestion = lambda user_id, mock_input: mock_output.structure()
    default_namespace.query_string = "test query"
    command = ChatCommand(default_namespace)
    command.run()

    captured = capsys.readouterr()
    assert "Requesting knowledge from AI" in captured.out.strip()


@pytest.mark.parametrize(
    ("test_args",),
    [
        ("",),
        ("   ",),
    ],
)
def test_query_command_invalid_inputs(test_args, capsys, default_namespace):
    """Test QueryCommand with invalid inputs"""
    default_namespace.query_string = test_args
    command = ChatCommand(default_namespace)
    command.run()

    captured = capsys.readouterr()
    assert (
        "\x1b[31m🙁 No input provided. Please provide input via file, stdin, or direct\nquery.\x1b[0m"
        in captured.err
    )


def test_register_subcommand():
    """Test register_subcommand function"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # Register the subcommand
    register_subcommand(subparsers)

    # Parse a test command
    args = parser.parse_args(["chat", "test query"])

    assert args.query_string == "test query"
    assert hasattr(args, "func")


@pytest.mark.parametrize(
    ("query_string", "stdin", "attachment"),
    (
        (
            "test query",
            "",
            "",
        ),
        (
            "",
            "stdin",
            "",
        ),
        ("", "", mock.MagicMock()),
        ("test query", "test stdin", mock.MagicMock()),
    ),
)
def test_command_factory(query_string, stdin, attachment, default_namespace):
    """Test _command_factory function"""
    default_namespace.query_string = query_string
    default_namespace.stdin = stdin
    default_namespace.attachment = attachment
    command = _command_factory(default_namespace)

    assert isinstance(command, ChatCommand)
    assert command._query == query_string
    assert command._stdin == stdin


@pytest.mark.parametrize(
    ("query_string", "stdin", "attachment", "expected"),
    (
        ("test query", None, None, "test query"),
        (None, "stdin", None, "stdin"),
        ("query", "stdin", None, "query stdin"),
        (None, None, "file query", "file query"),
        ("query", None, "file query", "query file query"),
        (None, "stdin", "file query", "stdin file query"),
        # Stdin in this case is ignored.
        ("test query", "test stdin", "file query", "test query file query"),
    ),
)
def test_get_input_source(
    query_string, stdin, attachment, expected, tmp_path, default_namespace
):
    """Test _command_factory function"""
    file_attachment = None

    if attachment:
        file_attachment = tmp_path / "test.txt"
        file_attachment.write_text(attachment)
        file_attachment = open(file_attachment, "r")

    default_namespace.query_string = query_string
    default_namespace.stdin = stdin
    default_namespace.attachment = file_attachment
    command = ChatCommand(default_namespace)

    output = command._get_input_source()

    assert output == expected


def test_get_inout_source_all_values_warning_message(
    capsys, tmp_path, default_namespace
):
    file_attachment = tmp_path / "test.txt"
    file_attachment.write_text("file")
    file_attachment = open(file_attachment, "r")
    default_namespace.query_string = "query"
    default_namespace.stdin = "stdin"
    default_namespace.attachment = file_attachment
    command = ChatCommand(default_namespace)

    output = command._get_input_source()

    assert output == "query file"
    captured = capsys.readouterr()
    assert (
        "\x1b[33m🤔 Using positional query and file input. Stdin will be ignored.\x1b[0m\n"
        in captured.err
    )


def test_get_input_source_value_error(default_namespace):
    command = ChatCommand(default_namespace)

    with pytest.raises(
        ValueError,
        match="No input provided. Please provide input via file, stdin, or direct query.",
    ):
        command._get_input_source()


@pytest.mark.parametrize(
    ("exception", "expected"),
    (
        (
            RequestFailedError("Test DBus Error"),
            "Test DBus Error",
        ),
        (
            MissingHistoryFileError("Test DBus Error"),
            "Test DBus Error",
        ),
        (
            CorruptedHistoryError("Test DBus Error"),
            "Test DBus Error",
        ),
    ),
)
def test_dbus_error_handling(
    exception, expected, mock_dbus_service, capsys, default_namespace
):
    """Test handling of DBus errors"""
    # Make ProcessQuery raise a DBus error
    mock_dbus_service.AskQuestion.side_effect = exception
    default_namespace.query_string = "test query"
    command = ChatCommand(default_namespace)
    command.run()

    # Verify error message in stdout
    captured = capsys.readouterr()
    assert expected in captured.err.strip()


@pytest.mark.parametrize(
    ("content", "expected"),
    (
        ("test", "test"),
        ("test ", "test"),
    ),
)
def test_parse_attachment_file(content, expected, tmp_path):
    file_attachment = tmp_path / "file.txt"
    file_attachment.write_text(content)
    file_attachment = open(file_attachment, mode="r")

    assert _parse_attachment_file(file_attachment) == expected


def test_parse_attachment_file_missing():
    assert not _parse_attachment_file(None)


def test_parse_attachment_file_exception(tmp_path):
    file_attachment = tmp_path / "file.txt"
    file_attachment.write_bytes(b"'\x80abc'")
    file_attachment = open(file_attachment, mode="r")

    with pytest.raises(
        ValueError, match="File appears to be binary or contains invalid text encoding"
    ):
        assert _parse_attachment_file(file_attachment)


def test_chat_management_list(mock_dbus_service, capsys, default_namespace):
    mock_dbus_service.GetAllChatFromUser = lambda user_id: ChatList(
        [ChatEntry()]
    ).structure()

    default_namespace.list = True

    ChatCommand(default_namespace).run()

    captured = capsys.readouterr()

    assert "Found a total of 1 chats:" in captured.out
    assert "0. Chat:" in captured.out


def test_chat_management_list_not_available(
    mock_dbus_service, capsys, default_namespace
):
    mock_dbus_service.GetAllChatFromUser = lambda user_id: ChatList([]).structure()

    default_namespace.list = True

    ChatCommand(default_namespace).run()

    captured = capsys.readouterr()

    assert "No chats available." in captured.out


def test_chat_management_delete(mock_dbus_service, capsys, default_namespace):
    mock_dbus_service.DeleteChatForUser = lambda user_id, name: None

    default_namespace.delete = "test"

    ChatCommand(default_namespace).run()

    captured = capsys.readouterr()

    assert "Chat test deleted successfully" in captured.out


def test_chat_management_delete_exception(mock_dbus_service, capsys, default_namespace):
    mock_dbus_service.DeleteChatForUser.side_effect = ChatNotFoundError(
        "chat not found"
    )

    default_namespace.delete = "test"
    assert ChatCommand(default_namespace).run() == 1
    captured = capsys.readouterr()

    assert "chat not found" in captured.err


def test_chat_management_delete_all(mock_dbus_service, capsys, default_namespace):
    mock_dbus_service.DeleteAllChatForUser = lambda user_id: None

    default_namespace.delete_all = True

    ChatCommand(default_namespace).run()

    captured = capsys.readouterr()

    assert "Deleted all chats successfully" in captured.out


def test_chat_management_delete_all_exception(
    mock_dbus_service, capsys, default_namespace
):
    mock_dbus_service.DeleteAllChatForUser.side_effect = ChatNotFoundError(
        "chat not found"
    )

    default_namespace.delete_all = True
    assert ChatCommand(default_namespace).run() == 1
    captured = capsys.readouterr()

    assert "chat not found" in captured.err


def test_create_chat_session(mock_dbus_service, default_namespace):
    mock_dbus_service.GetChatId = lambda user_id, name: "1"
    default_namespace.name = "test"
    assert ChatCommand(default_namespace)._create_chat_session("1") == "1"


def test_create_chat_session_exception(mock_dbus_service, default_namespace):
    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("no chat available")
    mock_dbus_service.CreateChat = lambda user_id, name, description: "1"
    default_namespace.name = "test"
    assert ChatCommand(default_namespace)._create_chat_session("1") == "1"
