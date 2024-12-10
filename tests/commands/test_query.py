from unittest.mock import Mock, patch

import pytest

from command_line_assistant.commands.query import QueryCommand, register_subcommand
from command_line_assistant.config import (
    Config,
)


@pytest.fixture
def query_command(mock_config):
    """Fixture to create a QueryCommand instance"""
    return QueryCommand("test query", mock_config)


def test_query_command_initialization(query_command):
    """Test QueryCommand initialization"""
    assert query_command._query == "test query"
    assert isinstance(query_command._config, Config)


@patch("command_line_assistant.commands.query.handle_query")
def test_query_command_run(mock_handle_query, query_command):
    """Test QueryCommand run method"""
    query_command.run()
    mock_handle_query.assert_called_once_with("test query", query_command._config)


@patch("command_line_assistant.commands.query.handle_query")
def test_query_command_with_empty_query(mock_handle_query, mock_config):
    """Test QueryCommand with empty query"""
    command = QueryCommand("", mock_config)
    command.run()
    mock_handle_query.assert_called_once_with("", mock_config)


def test_register_subcommand():
    """Test subcommand registration"""
    mock_parser = Mock()
    mock_subparser = Mock()
    mock_parser.add_parser.return_value = mock_subparser
    mock_config = Mock()

    register_subcommand(mock_parser, mock_config)

    # Verify parser configuration
    mock_parser.add_parser.assert_called_once_with("query", help="")
    mock_subparser.add_argument.assert_called_once_with(
        "query_string", nargs="?", help="Query string to be processed."
    )
    assert mock_subparser.set_defaults.called


@pytest.mark.parametrize(
    "query_string,expected",
    [
        ("normal query", "normal query"),
        ("", ""),
        ("complex query with spaces", "complex query with spaces"),
        ("query?with!special@chars", "query?with!special@chars"),
    ],
)
def test_query_command_different_inputs(mock_config, query_string, expected):
    """Test QueryCommand with different input strings"""
    command = QueryCommand(query_string, mock_config)
    assert command._query == expected


@patch("command_line_assistant.commands.query.handle_query")
def test_query_command_error_handling(mock_handle_query, query_command):
    """Test QueryCommand error handling"""
    mock_handle_query.side_effect = Exception("Test error")

    with pytest.raises(Exception) as exc_info:
        query_command.run()

    assert str(exc_info.value) == "Test error"
    mock_handle_query.assert_called_once()


def test_query_command_config_validation(mock_config):
    """Test QueryCommand with invalid config"""
    # Modify config to be invalid
    mock_config.backend.endpoint = ""

    command = QueryCommand("test query", mock_config)
    assert command._config.backend.endpoint == ""


@patch("command_line_assistant.commands.query.handle_query")
def test_query_command_with_special_characters(mock_handle_query, mock_config):
    """Test QueryCommand with special characters in query"""
    special_query = r"test\nquery\twith\rspecial\characters"
    command = QueryCommand(special_query, mock_config)
    command.run()
    mock_handle_query.assert_called_once_with(special_query, mock_config)
