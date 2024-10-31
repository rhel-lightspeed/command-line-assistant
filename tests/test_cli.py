import sys
from unittest import mock

import pytest

from command_line_assistant import cli


def mock_cli_arguments(args):
    """
    Return a list of cli arguments where the first one is always the name of
    the executable, followed by 'args'.
    """
    return sys.argv[0:1] + args


def test_get_args(monkeypatch):
    monkeypatch.setattr(sys, "argv", mock_cli_arguments(["test"]))
    monkeypatch.setattr(cli, "read_stdin", mock.Mock())
    parser, args = cli.get_args()

    assert parser
    assert args.query_string == "test"


def test_no_query_args(monkeypatch):
    monkeypatch.setattr(sys, "argv", mock_cli_arguments([]))
    # Empty output to make sure that there is nothing being assigned to args.query_string
    monkeypatch.setattr(cli, "read_stdin", lambda: "")

    with pytest.raises(SystemExit):
        cli.get_args()
