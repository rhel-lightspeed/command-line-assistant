import json
from unittest import mock

import pytest

from command_line_assistant.terminal import parser

TERMINAL_LOG_MOCK = [
    {
        "command": '\u001b]0;rolivier@fedora:~/Workspace/command-line-assistant\u0007\u001b[?2004h\u001b]633;A\u0007(command-line-assistant-py3.13) \u001b]633;A\u0007\u001b[m\u001b[0m\u001b[m\u001b[0m$\u001b[0m \u001b]633;B\u0007\u001b]633;B\u0007echo "test"',
        "output": "\u001b[?2004l",
    },
    {
        "command": "test\r\n\u001b]0;rolivier@fedora:~/Workspace/command-line-assistant\u0007\u001b[?2004h\u001b]633;A\u0007(command-line-assistant-py3.13) \u001b]633;A\u0007\u001b[m\u001b[0m\u001b[m\u001b[0m$\u001b[0m \u001b]633;B\u0007\u001b]633;B\u0007n\b\u001b[Kdnf log",
        "output": '\u001b[?2004l\rUnknown argument "log" for command "dnf5". Add "--help" for more information about the arguments.\r\nIt could be a command provided by a plugin, try: dnf5 install \'dnf5-command(log)\'',
    },
    {
        "command": "\u001b]0;rolivier@fedora:~/Workspace/command-line-assistant\u0007\u001b[?2004h\u001b]633;A\u0007(command-line-assistant-py3.13) \u001b]633;A\u0007\u001b[m\u001b[0m\u001b[m\u001b[0m$\u001b[0m \u001b]633;B\u0007\u001b]633;B\u0007",
        "output": "\u001b[?2004l\r\r\nexit",
    },
    {
        "command": "\u001b]0;rolivier@fedora:~/Workspace/command-line-assistant\u0007\u001b[?2004h\u001b]633;A\u0007(command-line-assistant-py3.13) \u001b]633;A\u0007\u001b[m\u001b[0m\u001b[m\u001b[0m$\u001b[0m \u001b]633;B\u0007\u001b]633;B\u0007",
        "output": "\u001b[?2004lblablabla]\r\r\nexit",
    },
]


@pytest.fixture(autouse=True)
def mock_terminal_log(monkeypatch, tmp_path):
    terminal_log_file = tmp_path / "terminal.log"
    monkeypatch.setattr(parser, "TERMINAL_CAPTURE_FILE", terminal_log_file)
    with terminal_log_file.open(mode="ab") as handler:
        for block in TERMINAL_LOG_MOCK:
            handler.write(json.dumps(block).encode() + b"\n")


def test_parse_terminal_output_file_not_present(monkeypatch, tmp_path):
    terminal_log_file = tmp_path / "test-file.log"
    monkeypatch.setattr(parser, "TERMINAL_CAPTURE_FILE", terminal_log_file)
    assert not parser.parse_terminal_output()


def test_parse_terminal_output():
    result = parser.parse_terminal_output()
    assert isinstance(result, list)
    # We don't count the last `exit` command
    assert len(result) == 2


def test_parse_terminal_output_failed_to_decode_json(monkeypatch):
    monkeypatch.setattr(
        json, "loads", mock.Mock(side_effect=json.JSONDecodeError("test", "test", 0))
    )
    result = parser.parse_terminal_output()
    assert isinstance(result, list)
    assert len(result) == 0
    assert not result


@pytest.mark.parametrize(
    ("index", "expected"), ((1, 'Unknown argument "log"'), (99, ""))
)
def test_find_output_by_index(index, expected):
    result = parser.find_output_by_index(index, TERMINAL_LOG_MOCK)
    assert expected in result


def test_clean_parsed_text():
    result = parser.clean_parsed_text("\u001b[?2004l\r\r\nexit")
    assert result == "exit"
