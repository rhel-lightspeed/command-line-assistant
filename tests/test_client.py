from unittest.mock import Mock, patch

import pytest
from dasbus.error import DBusError

from command_line_assistant.client import main
from command_line_assistant.constants import VERSION


def test_initialize_with_no_args(capsys):
    """Test initialize with no arguments - should print help and return 1"""
    with (
        patch("sys.argv", ["c"]),
        patch("command_line_assistant.client.read_stdin", lambda: None),
    ):
        result = main()
        captured = capsys.readouterr()

        assert result == 64  # os.EX_USAGE
        assert "usage:" in captured.out


@pytest.mark.parametrize(
    ("argv", "stdin"),
    (
        (
            ["c", "chat", "test", "query"],
            None,
        ),
        (["c"], "test from stdin"),
        (["c", "what is this?"], "error in line 1"),
    ),
)
def test_initialize_with_query_command(argv, stdin):
    """Test initialize with query command"""
    mock_command = Mock(return_value=0)

    with (
        patch("sys.argv", argv),
        patch("command_line_assistant.commands.cli.register_all_commands"),
        patch("command_line_assistant.client.read_stdin", lambda: stdin),
        patch("argparse.ArgumentParser.parse_args") as mock_parse,
    ):
        mock_parse.return_value.func = mock_command
        result = main()

        assert result == 0
        mock_command.assert_called_once()


def test_initialize_with_history_command():
    """Test initialize with history command"""
    mock_command = Mock(return_value=0)

    with (
        patch("sys.argv", ["c", "history", "--clear"]),
        patch("command_line_assistant.commands.cli.register_all_commands"),
        patch("command_line_assistant.client.read_stdin", lambda: None),
        patch("argparse.ArgumentParser.parse_args") as mock_parse,
    ):
        mock_parse.return_value.func = mock_command
        result = main()

        assert result == 0
        mock_command.assert_called_once()


def test_initialize_with_shell_command():
    """Test initialize with shell command"""
    mock_command = Mock(return_value=0)

    with (
        patch("sys.argv", ["c", "shell", "--enable-interactive"]),
        patch("command_line_assistant.commands.cli.register_all_commands"),
        patch("command_line_assistant.client.read_stdin", lambda: None),
        patch("argparse.ArgumentParser.parse_args") as mock_parse,
    ):
        mock_parse.return_value.func = mock_command
        result = main()

        assert result == 0
        mock_command.assert_called_once()


def test_initialize_with_version(capsys):
    """Test initialize with --version flag"""
    with (
        patch("sys.argv", ["c", "--version"]),
        patch("command_line_assistant.client.read_stdin", lambda: None),
    ):
        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert VERSION in captured.out


def test_initialize_with_help(capsys):
    """Test initialize with --help flag"""
    with (
        patch("sys.argv", ["c", "--help"]),
        patch("command_line_assistant.client.read_stdin", lambda: None),
    ):
        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "usage:" in captured.out


def test_initialize_bad_stdin(capsys, disable_stream_flush):
    with patch("command_line_assistant.client.read_stdin") as mock_stdin:
        mock_stdin.side_effect = ValueError("Binary input are not supported.")
        main()

    captured = capsys.readouterr()
    assert "🙁 \x1b[31mBinary input are not supported.\x1b[0m\n" in captured.out


def test_initialize_keyboard_interrupt(capsys, disable_stream_flush):
    with patch("command_line_assistant.client.read_stdin") as mock_stdin:
        mock_stdin.side_effect = KeyboardInterrupt("Interrupted")
        main()

    captured = capsys.readouterr()
    assert "🙁 \x1b[31mKeyboard interrupt detected. Exiting...\x1b[0m\n" in captured.out


@pytest.mark.parametrize(
    ("argv"),
    [
        (["c"]),  # Default to chat
        (["c", "chat"]),
        (["c", "shell"]),
    ],
)
def test_initialize_command_selection(argv, capsys):
    """Test command selection logic"""

    with (
        patch("sys.argv", argv),
        patch("command_line_assistant.client.read_stdin", lambda: None),
    ):
        result = main()

    captured = capsys.readouterr()
    assert "usage: c" in captured.out
    assert result == 64


@pytest.mark.parametrize(
    ("exception", "expected"),
    (
        (DBusError, "🙁 \x1b[31m🙁 \x1b[31mName is not active\x1b[0m\n\x1b[0m\n"),
        (
            RuntimeError,
            "🙁 \x1b[31mOops! Something went wrong while processing your request.\x1b[0m\n",
        ),
    ),
)
def test_exception_initialization_error(
    exception, expected, capsys, disable_stream_flush
):
    with patch("command_line_assistant.client.read_stdin") as mock_stdin:
        mock_stdin.side_effect = exception(expected)
        main()

    captured = capsys.readouterr()
    assert expected in captured.out


def test_command_registry_integration():
    """Test that the command registry is properly integrated"""
    with (
        patch("sys.argv", ["c", "--help"]),
        patch("command_line_assistant.client.read_stdin", lambda: None),
    ):
        with pytest.raises(SystemExit):
            main()


def test_command_exception_handling():
    """Test that command exceptions are handled properly"""
    mock_command = Mock(side_effect=ValueError("Test error"))

    with (
        patch("sys.argv", ["c", "chat", "test"]),
        patch("command_line_assistant.commands.cli.register_all_commands"),
        patch("command_line_assistant.client.read_stdin", lambda: None),
        patch("argparse.ArgumentParser.parse_args") as mock_parse,
    ):
        mock_parse.return_value.func = mock_command
        mock_parse.return_value.plain = False
        result = main()

        assert result == 65  # os.EX_DATAERR
        mock_command.assert_called_once()
