from unittest.mock import MagicMock, patch

import pytest

from command_line_assistant.commands.history import (
    HistoryCommand,
    _command_factory,
    register_subcommand,
)
from command_line_assistant.dbus.constants import HISTORY_IDENTIFIER


@pytest.fixture
def mock_get_proxy(mock_proxy):
    """Mock the get_proxy method."""
    with patch.object(HISTORY_IDENTIFIER, "get_proxy", return_value=mock_proxy):
        yield mock_proxy


def test_history_command_clear_success(mock_get_proxy):
    """Test successful history clear operation."""
    cmd = HistoryCommand(clear=True)
    cmd.run()

    mock_get_proxy.ClearHistory.assert_called_once()


def test_history_command_clear_failure(mock_get_proxy, caplog):
    """Test failed history clear operation."""
    from dasbus.error import DBusError

    # Configure mock to raise DBusError
    mock_get_proxy.ClearHistory.side_effect = DBusError("Failed to clear history")

    cmd = HistoryCommand(clear=True)

    with pytest.raises(DBusError):
        cmd.run()

    assert "Failed to clean the history" in caplog.text


def test_history_command_no_clear(mock_get_proxy):
    """Test history command without clear flag."""
    cmd = HistoryCommand(clear=False)
    cmd.run()

    mock_get_proxy.ClearHistory.assert_not_called()


def test_register_subcommand():
    """Test registration of history subcommand."""
    parser = MagicMock()
    subparser = MagicMock()
    parser.add_parser.return_value = subparser

    register_subcommand(parser)

    # Verify parser configuration
    parser.add_parser.assert_called_once_with(
        "history", help="Manage conversation history"
    )

    # Verify arguments added to subparser
    subparser.add_argument.assert_called_once_with(
        "--clear", action="store_true", help="Clear the history."
    )

    # Verify defaults set
    assert hasattr(subparser, "set_defaults")


def test_command_factory():
    """Test the command factory creates correct command instance."""
    from argparse import Namespace

    args = Namespace(clear=True)
    cmd = _command_factory(args)

    assert isinstance(cmd, HistoryCommand)
    assert cmd._clear is True
