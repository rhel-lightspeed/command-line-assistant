from unittest.mock import Mock, patch

import pytest

from command_line_assistant.commands.record import RecordCommand


@pytest.fixture
def record_command(mock_config):
    """Fixture for RecordCommand instance"""
    return RecordCommand(mock_config)


class TestRecordCommand:
    def test_init(self, record_command, mock_config):
        """Test RecordCommand initialization"""
        assert record_command._config == mock_config

    @patch("command_line_assistant.commands.record.handle_script_session")
    @patch("os.path.exists")
    def test_run_with_existing_file(
        self, mock_exists, mock_script_session, record_command
    ):
        """Test run() when output file exists"""
        mock_exists.return_value = True
        record_command.run()
        mock_script_session.assert_called_once_with(record_command._config.output.file)

    @patch("command_line_assistant.commands.record.handle_script_session")
    @patch("os.path.exists")
    @patch("sys.exit")
    def test_run_without_file_enforced(
        self, mock_exit, mock_exists, mock_script_session, record_command
    ):
        """Test run() when output file doesn't exist and script is enforced"""
        mock_exists.return_value = False
        record_command.run()
        mock_script_session.assert_called_once_with(record_command._config.output.file)

    @patch("command_line_assistant.commands.record.handle_script_session")
    @patch("os.path.exists")
    def test_run_without_enforcement(
        self, mock_exists, mock_script_session, mock_config
    ):
        """Test run() when script enforcement is disabled"""
        mock_config.output.enforce_script = False
        command = RecordCommand(mock_config)
        mock_exists.return_value = False

        command.run()
        mock_script_session.assert_called_once_with(command._config.output.file)


def test_register_subcommand(mock_config):
    """Test register_subcommand function"""
    mock_parser = Mock()
    mock_parser.add_parser.return_value = mock_parser

    from command_line_assistant.commands.record import register_subcommand

    register_subcommand(mock_parser, mock_config)

    mock_parser.add_parser.assert_called_once_with(
        "record", help="Start a recording session for script output."
    )
    assert mock_parser.set_defaults.called


def test_command_factory(mock_config):
    """Test _command_factory function"""
    from command_line_assistant.commands.record import _command_factory

    command = _command_factory(mock_config)
    assert isinstance(command, RecordCommand)
    assert command._config == mock_config
