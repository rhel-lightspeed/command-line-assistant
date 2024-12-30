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
    ("args", "stdin", "expected"),
    [
        # When we just call `c` and do anything, we print help
        (["c"], None, []),
        (["c", "query", "test query"], None, ["query", "test query"]),
        (["c", "how to list files?"], None, ["query", "how to list files?"]),
        # When we read from stdin, we just return the `query` command without the query_string part.
        (["c"], "query from stdin", ["query"]),
        # It still should return the query command plus the query string
        (
            ["c", "what is this madness?"],
            "query from stdin",
            ["query", "what is this madness?"],
        ),
        (["/usr/bin/c", "test query"], None, ["query", "test query"]),
        (["/usr/bin/c", "history"], None, ["history"]),
    ],
)
def test_add_default_command(args, stdin, expected):
    """Test adding default 'query' command when no command is specified"""
    assert cli.add_default_command(stdin, args) == expected


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
