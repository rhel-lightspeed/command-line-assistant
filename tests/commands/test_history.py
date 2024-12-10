from argparse import ArgumentParser, Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

from command_line_assistant.commands import history
from command_line_assistant.commands.history import (
    HistoryCommand,
    _command_factory,
)


@pytest.fixture
def history_command():
    """Fixture to create a HistoryCommand instance"""
    return HistoryCommand(clear=True)


@pytest.fixture
def history_command_no_clear():
    """Fixture to create a HistoryCommand instance"""
    return HistoryCommand(clear=False)


class TestHistoryCommand:
    def test_init(self, history_command):
        """Test HistoryCommand initialization"""
        assert history_command._clear is True

    @patch("command_line_assistant.commands.history.handle_history_write")
    def test_run_with_clear(self, mock_history_write, history_command):
        """Test run() method when clear=True"""
        history_command.run()
        mock_history_write.assert_called_once_with(
            Path("/tmp/test_history.json"), [], ""
        )

    @patch("command_line_assistant.commands.history.handle_history_write")
    def test_run_without_clear(self, mock_history_write, history_command_no_clear):
        """Test run() method when clear=False"""
        history_command_no_clear.run()
        mock_history_write.assert_not_called()


def test_register_subcommand():
    """Test register_subcommand function"""
    parser = ArgumentParser()
    sub_parser = parser.add_subparsers()

    history.register_subcommand(sub_parser)

    parser.parse_args(["history", "--clear"])


def test_command_factory():
    """Test _command_factory function"""

    args = Namespace(clear=True)
    command = _command_factory(args)

    assert isinstance(command, HistoryCommand)
    assert command._clear is True
