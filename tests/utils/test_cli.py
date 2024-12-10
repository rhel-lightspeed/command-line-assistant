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


def test_create_argument_parser():
    """Test create_argument_parser returns parser and subparser"""
    parser, commands_parser = cli.create_argument_parser()
    assert parser is not None
    assert commands_parser is not None
    assert parser.description is not None
    assert commands_parser.dest == "command"


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["c"], []),
        (["c", "query", "test query"], ["query", "test query"]),
        (["c", "how to list files?"], ["query", "how to list files?"]),
        (["/usr/bin/c", "test query"], ["query", "test query"]),
        # When we just call `c` and do anything, we print help
        (
            [],
            [],
        ),
        (["/usr/bin/c", "history"], ["history"]),
    ],
)
def test_add_default_command(args, expected):
    """Test adding default 'query' command when no command is specified"""
    assert cli.add_default_command(args) == expected


@pytest.mark.parametrize(
    ("argv", "expected"),
    (
        (["query"], "query"),
        (["--version"], "--version"),
        (["--help"], "--help"),
        (["--clear"], None),
    ),
)
def test_subcommand_used(argv, expected):
    assert cli._subcommand_used(argv) == expected
