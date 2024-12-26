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
        mock_proxy.RetrieveAnswer = lambda: Message.to_structure(mock_output)

        yield mock_proxy


def test_query_command_initialization():
    """Test QueryCommand initialization"""
    query = "test query"
    command = QueryCommand(query)
    assert command._query == query


@pytest.mark.parametrize(
    (
        "test_input",
        "expected_output",
    ),
    [
        ("how to list files?", "Use the ls command"),
        ("what is linux?", "Linux is an operating system"),
    ],
)
def test_query_command_run(mock_dbus_service, test_input, expected_output, capsys):
    """Test QueryCommand run method with different inputs"""
    # Setup mock response for this specific test
    mock_output = Message()
    mock_output.message = expected_output
    mock_dbus_service.RetrieveAnswer = lambda: Message.to_structure(mock_output)

    # Create and run command
    command = QueryCommand(test_input)
    command.run()

    # Verify ProcessQuery was called with correct input
    expected_input = Message()
    expected_input.message = test_input
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
    mock_dbus_service.RetrieveAnswer = lambda: Message.to_structure(mock_output)

    command = QueryCommand("test query")
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
    command = QueryCommand(test_args)
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


def test_command_factory():
    """Test _command_factory function"""

    from command_line_assistant.commands.query import _command_factory

    args = Namespace(query_string="test query")
    command = _command_factory(args)

    assert isinstance(command, QueryCommand)
    assert command._query == "test query"


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

    command = QueryCommand("test query")
    command.run()

    # Verify error message in stdout
    captured = capsys.readouterr()
    assert expected in captured.out.strip()


def test_query_with_special_characters(mock_dbus_service, capsys):
    """Test query containing special characters"""
    special_query = "test!@#$%^&*()_+ query"
    expected_response = "response with special chars !@#$"

    mock_output = Message()
    mock_output.message = expected_response
    mock_dbus_service.RetrieveAnswer = lambda: Message.to_structure(mock_output)

    command = QueryCommand(special_query)
    command.run()

    expected_input = Message()
    expected_input.message = special_query
    mock_dbus_service.ProcessQuery.assert_called_once_with(
        Message.to_structure(expected_input)
    )

    captured = capsys.readouterr()
    assert expected_response in captured.out.strip()
