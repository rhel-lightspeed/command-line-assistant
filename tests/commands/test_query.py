from argparse import ArgumentParser, Namespace
from io import StringIO
from unittest import mock
from unittest.mock import patch

import pytest

from command_line_assistant.commands.query import (
    QueryCommand,
    _command_factory,
    register_subcommand,
)
from command_line_assistant.dbus.exceptions import (
    CorruptedHistoryError,
    MissingHistoryFileError,
    RequestFailedError,
)
from command_line_assistant.dbus.structures import Message


# Mock the entire DBus service/constants module
@pytest.fixture(autouse=True)
def mock_dbus_service(mock_proxy):
    """Fixture to mock DBus service and automatically use it for all tests"""
    with patch(
        "command_line_assistant.commands.query.QUERY_IDENTIFIER"
    ) as mock_service:
        # Create a mock proxy that will be returned by get_proxy()
        mock_service.get_proxy.return_value = mock_proxy

        # Setup default mock response
        mock_output = Message()
        mock_output.message = "default mock response"
        mock_output.user = "mock"
        mock_proxy.RetrieveAnswer = lambda: Message.to_structure(mock_output)

        yield mock_proxy


def test_query_command_initialization():
    """Test QueryCommand initialization"""
    query = "test query"
    command = QueryCommand(query, None)
    assert command._query == query


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
    mock_output = Message()
    mock_output.message = expected_output
    mock_output.user = "mock"
    mock_dbus_service.RetrieveAnswer = lambda: Message.to_structure(mock_output)

    with patch("command_line_assistant.commands.query.getpass.getuser") as mock_getuser:
        mock_getuser.return_value = "mock"
        # Create and run command
        command = QueryCommand(test_input, None)
        command.run()

    # Verify ProcessQuery was called with correct input
    expected_input = Message()
    expected_input.message = test_input
    expected_input.user = "mock"
    mock_dbus_service.ProcessQuery.assert_called_once_with(
        Message.to_structure(expected_input)
    )

    # Verify output was printed
    captured = capsys.readouterr()
    assert expected_output in captured.out.strip()


def test_query_command_empty_response(mock_dbus_service, capsys):
    """Test QueryCommand handling empty response"""
    # Setup empty response
    mock_output = Message()
    mock_output.message = ""
    mock_output.user = "mock"
    mock_dbus_service.RetrieveAnswer = lambda: Message.to_structure(mock_output)

    command = QueryCommand("test query", None)
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
def test_query_command_invalid_inputs(mock_dbus_service, test_args, capsys):
    """Test QueryCommand with invalid inputs"""
    command = QueryCommand(test_args, None)
    command.run()

    captured = capsys.readouterr()
    assert (
        "\x1b[31m🙁 No input provided. Please provide input via file, stdin, or direct\nquery.\x1b[0m"
        in captured.out
    )


def test_register_subcommand():
    """Test register_subcommand function"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # Register the subcommand
    register_subcommand(subparsers)

    # Parse a test command
    args = parser.parse_args(["query", "test query"])

    assert args.query_string == "test query"
    assert hasattr(args, "func")


@pytest.mark.parametrize(
    ("query_string", "stdin", "input"),
    (
        (
            "test query",
            None,
            None,
        ),
        (
            None,
            "stdin",
            None,
        ),
        (None, None, mock.Mock()),
        ("test query", "test stdin", mock.Mock()),
    ),
)
def test_command_factory(query_string, stdin, input):
    """Test _command_factory function"""
    options = {"query_string": query_string, "stdin": stdin, "input": input}
    args = Namespace(**options)
    command = _command_factory(args)

    assert isinstance(command, QueryCommand)
    assert command._query == query_string
    assert command._stdin == stdin


@pytest.mark.parametrize(
    ("query_string", "stdin", "input", "expected"),
    (
        ("test query", None, None, "test query"),
        (None, "stdin", None, "stdin"),
        ("query", "stdin", None, "query stdin"),
        (None, None, StringIO("file query"), "file query"),
        ("query", None, StringIO("file query"), "query file query"),
        (None, "stdin", StringIO("file query"), "stdin file query"),
        # Stdin in this case is ignored.
        ("test query", "test stdin", StringIO("file query"), "test query file query"),
    ),
)
def test_get_input_source(query_string, stdin, input, expected):
    """Test _command_factory function"""
    options = {"query_string": query_string, "stdin": stdin, "input": input}
    command = QueryCommand(**options)

    output = command._get_input_source()

    assert output == expected


@pytest.mark.parametrize(
    ("input_file",),
    (
        ("\x7fELF",),
        ("%PDF",),
        ("PK\x03\x04",),
    ),
)
def test_get_input_source_binary_file(input_file):
    options = {"query_string": None, "stdin": None, "input": StringIO(input_file)}
    command = QueryCommand(**options)
    with pytest.raises(ValueError, match="File appears to be binary"):
        command._get_input_source()


def test_get_inout_source_all_values_warning_message(capsys):
    options = {"query_string": "query", "stdin": "stdin", "input": StringIO("file")}
    command = QueryCommand(**options)

    output = command._get_input_source()

    assert output == "query file"
    captured = capsys.readouterr()
    assert (
        "\x1b[33m🤔 Using positional query and file input. Stdin will be ignored.\x1b[0m\n"
        in captured.err
    )


def test_get_input_source_value_error():
    command = QueryCommand(None, None, None)

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
    mock_dbus_service.ProcessQuery.side_effect = exception

    command = QueryCommand("test query", None)
    command.run()

    # Verify error message in stdout
    captured = capsys.readouterr()
    assert expected in captured.out.strip()
