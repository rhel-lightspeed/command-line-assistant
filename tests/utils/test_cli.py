import select
import sys

import pytest

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


@pytest.mark.parametrize(
    ("input_args", "expected"),
    [
        (["script_name"], []),
        (["script_name", "history", "--clear"], ["history", "--clear"]),
        (["script_name", "how to list files"], ["query", "how to list files"]),
    ],
)
def test_add_default_command(input_args, expected):
    """Test add_default_command with various inputs"""
    args = cli.add_default_command(input_args)
    assert args == expected


@pytest.mark.parametrize(
    ("input_args", "expected"),
    [
        (["script_name", "query", "some text"], "query"),
        (["script_name", "history", "--clear"], "history"),
        (["script_name", "--version"], "--version"),
        (["script_name", "--help"], "--help"),
        (["script_name", "some text"], None),
    ],
)
def test_subcommand_used(input_args, expected):
    """Test _subcommand_used with various inputs"""
    assert cli._subcommand_used(input_args) == expected


def test_create_argument_parser():
    """Test create_argument_parser returns parser and subparser"""
    parser, commands_parser = cli.create_argument_parser()
    assert parser is not None
    assert commands_parser is not None
    assert parser.description is not None
    assert commands_parser.dest == "command"
