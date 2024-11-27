import sys

import pytest

from command_line_assistant.commands import utils


@pytest.mark.parametrize(
    ("argv", "expected"),
    (
        (["test query"], ["query", "test query"]),
        # When we just call `c` and do anything, we print help
        (
            [],
            [],
        ),
        (["history"], ["history"]),
    ),
)
def test_add_default_command(argv, expected, monkeypatch):
    monkeypatch.setattr(sys, "argv", argv)
    assert utils.add_default_command(argv) == expected


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
    assert utils._subcommand_used(argv) == expected
