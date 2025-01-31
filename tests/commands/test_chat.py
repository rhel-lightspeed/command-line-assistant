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
    CorruptedHistoryError,
    MissingHistoryFileError,
    RequestFailedError,
)
from command_line_assistant.dbus.structures.chat import Response


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


def test_query_command_initialization():
    """Test QueryCommand initialization"""
    args = Namespace(query_string="test query", stdin=None, attachment=None)
    command = ChatCommand(args)
    assert command._query == args.query_string


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
def test_query_command_run(mock_dbus_service, test_input, expected_output, capsys):
    """Test QueryCommand run method with different inputs"""
    # Setup mock response for this specific test
    mock_output = Response(expected_output)
    mock_dbus_service.AskQuestion = (
        lambda chat_id, user_id, mock_input: mock_output.structure()
    )

    args = Namespace(
        query_string=test_input,
        stdin=None,
        attachment=None,
        list=None,
        delete=None,
        delete_all=None,
        name=None,
        description=None,
    )
    command = ChatCommand(args)
    command.run()

    # Verify output was printed
    captured = capsys.readouterr()
    assert expected_output in captured.out.strip()


def test_query_command_empty_response(mock_dbus_service, capsys):
    """Test QueryCommand handling empty response"""
    # Setup empty response
    mock_output = Response("")
    mock_dbus_service.AskQuestion = (
        lambda chat_id, user_id, mock_input: mock_output.structure()
    )

    args = Namespace(
        query_string="test query",
        stdin=None,
        attachment=None,
        list=None,
        delete=None,
        delete_all=None,
        name=None,
        description=None,
    )
    command = ChatCommand(args)
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
def test_query_command_invalid_inputs(test_args, capsys):
    """Test QueryCommand with invalid inputs"""
    args = Namespace(
        query_string=test_args,
        stdin=None,
        attachment=None,
        list=None,
        delete=None,
        delete_all=None,
        name=None,
        description=None,
    )
    command = ChatCommand(args)
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
def test_command_factory(query_string, stdin, attachment):
    """Test _command_factory function"""
    options = {"query_string": query_string, "stdin": stdin, "attachment": attachment}
    args = Namespace(**options)
    command = _command_factory(args)

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
def test_get_input_source(query_string, stdin, attachment, expected, tmp_path):
    """Test _command_factory function"""
    file_attachment = None

    if attachment:
        file_attachment = tmp_path / "test.txt"
        file_attachment.write_text(attachment)
        file_attachment = open(file_attachment, "r")

    args = Namespace(query_string=query_string, stdin=stdin, attachment=file_attachment)
    command = ChatCommand(args)

    output = command._get_input_source()

    assert output == expected


def test_get_inout_source_all_values_warning_message(capsys, tmp_path):
    file_attachment = tmp_path / "test.txt"
    file_attachment.write_text("file")
    file_attachment = open(file_attachment, "r")

    args = Namespace(
        query_string="query",
        stdin="stdin",
        attachment=file_attachment,
        list=None,
        delete=None,
        delete_all=None,
        name=None,
        description=None,
    )
    command = ChatCommand(args)

    output = command._get_input_source()

    assert output == "query file"
    captured = capsys.readouterr()
    assert (
        "\x1b[33m🤔 Using positional query and file input. Stdin will be ignored.\x1b[0m\n"
        in captured.err
    )


def test_get_input_source_value_error():
    args = Namespace(query_string=None, stdin=None, attachment=None)
    command = ChatCommand(args)

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
def test_dbus_error_handling(exception, expected, mock_dbus_service, capsys):
    """Test handling of DBus errors"""
    # Make ProcessQuery raise a DBus error
    mock_dbus_service.AskQuestion.side_effect = exception

    args = Namespace(
        query_string="test query",
        stdin=None,
        attachment=None,
        list=None,
        delete=None,
        delete_all=None,
        name=None,
        description=None,
    )
    command = ChatCommand(args)
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
