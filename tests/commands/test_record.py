from argparse import ArgumentParser
from pathlib import Path
from unittest.mock import patch

import pytest

from command_line_assistant.commands.record import RecordCommand, register_subcommand


@pytest.fixture
def record_command():
    """Fixture to create a RecordCommand instance."""
    test_output_file = "/tmp/test_output.txt"
    return RecordCommand(test_output_file)


@pytest.fixture
def parser():
    """Fixture to create an ArgumentParser instance."""
    parser = ArgumentParser()
    return parser.add_subparsers()


def test_init(record_command):
    """Test initialization of RecordCommand."""
    assert record_command._output_file == "/tmp/test_output.txt"


@patch("command_line_assistant.commands.record.handle_script_session")
def test_run(mock_handle_script_session, record_command):
    """Test the run method of RecordCommand."""
    record_command.run()

    # Verify handle_script_session was called with correct path
    mock_handle_script_session.assert_called_once_with(Path("/tmp/test_output.txt"))


@patch("command_line_assistant.commands.record.handle_script_session")
def test_run_with_empty_output_file(mock_handle_script_session):
    """Test the run method with empty output file."""
    record_command = RecordCommand("")
    record_command.run()

    # Verify handle_script_session was called with empty path
    mock_handle_script_session.assert_called_once_with(Path(""))


@patch("command_line_assistant.commands.record.handle_script_session")
def test_run_with_error(mock_handle_script_session, record_command):
    """Test the run method when handle_script_session raises an exception."""
    mock_handle_script_session.side_effect = Exception("Script session error")

    with pytest.raises(Exception) as exc_info:
        record_command.run()

    assert str(exc_info.value) == "Script session error"
    mock_handle_script_session.assert_called_once()


def test_register_subcommand(parser):
    """Test registration of subcommand in parser."""
    # Register subcommand
    register_subcommand(parser)

    # Create parent parser to test argument parsing
    parent_parser = ArgumentParser()
    subparsers = parent_parser.add_subparsers()
    register_subcommand(subparsers)

    # Parse args with record command
    args = parent_parser.parse_args(["record"])

    # Verify the command creates correct RecordCommand instance
    command = args.func(args)
    assert isinstance(command, RecordCommand)


@pytest.mark.parametrize(
    ("output_file", "expected_path"),
    [
        ("/tmp/test.txt", Path("/tmp/test.txt")),
        ("", Path("")),
        ("/var/log/output.log", Path("/var/log/output.log")),
    ],
)
@patch("command_line_assistant.commands.record.handle_script_session")
def test_record_command_different_paths(
    mock_handle_script_session, output_file, expected_path
):
    """Test RecordCommand with different output file paths."""
    command = RecordCommand(output_file)
    command.run()
    mock_handle_script_session.assert_called_once_with(expected_path)


def test_record_command_attributes():
    """Test RecordCommand instance attributes."""
    output_file = "/tmp/test_output.txt"
    command = RecordCommand(output_file)

    assert hasattr(command, "_output_file")
    assert command._output_file == output_file
    assert hasattr(command, "run")
    assert callable(command.run)
