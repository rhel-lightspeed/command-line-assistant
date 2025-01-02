from argparse import ArgumentParser, Namespace
from unittest.mock import patch

import pytest

from command_line_assistant.commands.query import QueryCommand, register_subcommand
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
def test_query_command_invalid_inputs(mock_dbus_service, test_args):
    """Test QueryCommand with invalid inputs"""
    command = QueryCommand(test_args, None)
    command.run()
    # Verify DBus calls still happen even with invalid input
    mock_dbus_service.ProcessQuery.assert_called_once()


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
    ("query_string", "stdin"),
    (
        (
            "test query",
            None,
        ),
        (None, "stdin"),
        ("test query", "test stdin"),
    ),
)
def test_command_factory(query_string, stdin):
    """Test _command_factory function"""

    from command_line_assistant.commands.query import _command_factory

    args = (
        Namespace(query_string=query_string, stdin=stdin)
        if stdin
        else Namespace(query_string=query_string)
    )
    command = _command_factory(args)

    assert isinstance(command, QueryCommand)
    assert command._query == query_string
    assert command._stdin == stdin


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
