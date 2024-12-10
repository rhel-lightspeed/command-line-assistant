from argparse import ArgumentParser, Namespace
from unittest.mock import patch

import pytest

from command_line_assistant.commands.history import (
    HistoryCommand,
    _command_factory,
    register_subcommand,
)


@pytest.fixture
def history_command(mock_config):
    """Fixture to create a HistoryCommand instance"""
    return HistoryCommand(clear=True, config=mock_config)


@pytest.fixture
def history_command_no_clear(mock_config):
    """Fixture to create a HistoryCommand instance"""
    return HistoryCommand(clear=False, config=mock_config)


class TestHistoryCommand:
    def test_init(self, history_command, mock_config):
        """Test HistoryCommand initialization"""
        assert history_command._clear is True
        assert history_command._config == mock_config

    @patch("command_line_assistant.commands.history.handle_history_write")
    def test_run_with_clear(self, mock_history_write, history_command):
        """Test run() method when clear=True"""
        history_command.run()
        mock_history_write.assert_called_once_with(history_command._config, [], "")

    @patch("command_line_assistant.commands.history.handle_history_write")
    def test_run_without_clear(self, mock_history_write, history_command_no_clear):
        """Test run() method when clear=False"""
        history_command_no_clear.run()
        mock_history_write.assert_not_called()

    @patch("command_line_assistant.commands.history.handle_history_write")
    def test_run_with_clear_and_disabled_history(self, mock_history_write, mock_config):
        """Test run() method when history is disabled"""
        mock_config.history.enabled = False
        command = HistoryCommand(clear=True, config=mock_config)
        command.run()
        mock_history_write.assert_called_once_with(command._config, [], "")


def test_register_subcommand(mock_config):
    """Test register_subcommand function"""
    parser = ArgumentParser()
    sub_parser = parser.add_subparsers()

    register_subcommand(sub_parser, mock_config)

    parser.parse_args(["history", "--clear"])


def test_command_factory(mock_config):
    """Test _command_factory function"""

    args = Namespace(clear=True)
    command = _command_factory(args, mock_config)

    assert isinstance(command, HistoryCommand)
    assert command._clear is True
    assert command._config == mock_config
