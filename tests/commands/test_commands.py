import sys

import pytest

from command_line_assistant.utils import cli


@pytest.mark.parametrize(
    ("argv", "expected"),
    (
        (["/usr/bin/c", "test query"], ["query", "test query"]),
        # When we just call `c` and do anything, we print help
        (
            [],
            [],
        ),
        (["/usr/bin/c", "history"], ["history"]),
    ),
)
def test_add_default_command(argv, expected, monkeypatch):
    monkeypatch.setattr(sys, "argv", argv)
    assert cli.add_default_command(argv) == expected


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
