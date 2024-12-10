import select
import sys

from command_line_assistant.utils import cli


def test_read_stdin(monkeypatch):
    # Mock select.select to simulate user input
    def mock_select(*args, **kwargs):
        return [sys.stdin], [], []

    monkeypatch.setattr(select, "select", mock_select)

    # Mock sys.stdin.readline to return the desired input
    monkeypatch.setattr(sys.stdin, "read", lambda: "test\n")

    assert cli.read_stdin() == "test"


def test_read_stdin_no_input(monkeypatch):
    # Mock select.select to simulate user input
    def mock_select(*args, **kwargs):
        return [], [], []

    monkeypatch.setattr(select, "select", mock_select)

    assert not cli.read_stdin()


def test_add_default_command_no_args():
    """Test add_default_command with no arguments"""
    args = cli.add_default_command(["script_name"])
    assert args == []


def test_add_default_command_with_subcommand():
    """Test add_default_command with explicit subcommand"""
    args = cli.add_default_command(["script_name", "history", "--clear"])
    assert args == ["history", "--clear"]


def test_add_default_command_no_subcommand():
    """Test add_default_command adds query command when no subcommand given"""
    args = cli.add_default_command(["script_name", "how to list files"])
    assert args == ["query", "how to list files"]


def test_subcommand_used_query():
    """Test _subcommand_used detects query command"""
    assert cli._subcommand_used(["script_name", "query", "some text"]) == "query"


def test_subcommand_used_history():
    """Test _subcommand_used detects history command"""
    assert cli._subcommand_used(["script_name", "history", "--clear"]) == "history"


def test_subcommand_used_parent_args():
    """Test _subcommand_used detects parent args"""
    assert cli._subcommand_used(["script_name", "--version"]) == "--version"
    assert cli._subcommand_used(["script_name", "--help"]) == "--help"


def test_subcommand_used_none():
    """Test _subcommand_used returns None when no subcommand found"""
    assert cli._subcommand_used(["script_name", "some text"]) is None


def test_create_argument_parser():
    """Test create_argument_parser returns parser and subparser"""
    parser, commands_parser = cli.create_argument_parser()
    assert parser is not None
    assert commands_parser is not None
    assert parser.description is not None
    assert commands_parser.dest == "command"
