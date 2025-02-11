import select
import sys
from unittest.mock import patch

import pytest

from command_line_assistant.utils import cli

MOCK_OS_RELEASE = """
NAME="Red Hat Enterprise Linux"
VERSION="10.0 (Coughlan)"
ID="rhel"
ID_LIKE="centos fedora"
VERSION_ID="10.0"
PLATFORM_ID="platform:el10"
PRETTY_NAME="Red Hat Enterprise Linux 10.0 Beta (Coughlan)"
ANSI_COLOR="0;31"
LOGO="fedora-logo-icon"
CPE_NAME="cpe:/o:redhat:enterprise_linux:10::baseos"
HOME_URL="https://www.redhat.com/"
VENDOR_NAME="Red Hat"
VENDOR_URL="https://www.redhat.com/"
DOCUMENTATION_URL="https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/10"
BUG_REPORT_URL="https://issues.redhat.com/"

REDHAT_BUGZILLA_PRODUCT="Red Hat Enterprise Linux 10"
REDHAT_BUGZILLA_PRODUCT_VERSION=10.0
REDHAT_SUPPORT_PRODUCT="Red Hat Enterprise Linux"
REDHAT_SUPPORT_PRODUCT_VERSION="10.0 Beta"
"""


def test_command_context_initialization():
    command_context = cli.CommandContext()
    assert isinstance(command_context.username, str)
    assert isinstance(command_context.effective_user_id, int)
    assert isinstance(command_context.os_release, dict)
    assert command_context.os_release


def test_command_context_os_release_not_found(tmp_path):
    os_release = tmp_path / "not_found"

    with patch("command_line_assistant.utils.cli.OS_RELEASE_PATH", os_release):
        with pytest.raises(ValueError, match="OS Release file not found"):
            cli.CommandContext()


def test_command_context_parse_os_release(tmp_path):
    os_release_file = tmp_path / "os-release"
    os_release_file.write_text(MOCK_OS_RELEASE)
    with patch("command_line_assistant.utils.cli.OS_RELEASE_PATH", os_release_file):
        context = cli.CommandContext()
        assert isinstance(context.os_release, dict)
        assert "name" in context.os_release
        assert context.os_release["name"] == "Red Hat Enterprise Linux"


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


def test_read_stdin_value_error(monkeypatch):
    # Mock select.select to simulate user input
    def mock_select(*args, **kwargs):
        return [sys.stdin], [], []

    monkeypatch.setattr(select, "select", mock_select)
    monkeypatch.setattr(sys.stdin, "read", lambda: b"'\x80abc'".decode())

    with pytest.raises(ValueError, match="Binary input are not supported."):
        cli.read_stdin()


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
        (["c", "chat", "test query"], None, ["chat", "test query"]),
        (["c", "how to list files?"], None, ["chat", "how to list files?"]),
        # When we read from stdin, we just return the `query` command without the query_string part.
        (["c"], "query from stdin", ["chat"]),
        # It still should return the query command plus the query string
        (
            ["c", "what is this madness?"],
            "query from stdin",
            ["chat", "what is this madness?"],
        ),
        (["/usr/bin/c", "test query"], None, ["chat", "test query"]),
        (["/usr/bin/c", "history"], None, ["history"]),
        (["/usr/bin/c", "shell"], None, ["shell"]),
    ],
)
def test_add_default_command(args, stdin, expected):
    """Test adding default 'query' command when no command is specified"""
    assert cli.add_default_command(stdin, args) == expected


@pytest.mark.parametrize(
    ("argv", "expected"),
    (
        (["chat"], "chat"),
        (["--debug"], None),
        (["--version"], None),
        (["--help"], None),
        (["--clear"], None),
    ),
)
def test_subcommand_used(argv, expected):
    assert cli._subcommand_used(argv) == expected
