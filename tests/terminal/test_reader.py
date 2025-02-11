import json
import os
from unittest import mock
from unittest.mock import patch

import pytest

from command_line_assistant.terminal import reader
from command_line_assistant.terminal.reader import TerminalRecorder, start_capturing


@pytest.fixture
def mock_pty_spawn():
    with patch("pty.spawn", return_value=0) as mock_spawn:
        yield mock_spawn


def test_start_capturing(mock_pty_spawn, monkeypatch, tmp_path):
    terminal_log = tmp_path / "terminal.log"
    monkeypatch.setattr(reader, "OUTPUT_FILE_NAME", terminal_log)
    monkeypatch.setenv("SHELL", "/usr/bin/bash")
    monkeypatch.setenv(
        "CLA_USER_SHELL_PROMPT_COMMAND",
        r'printf "\033]0;%s@%s:%s\007" "${USER}" "${HOSTNAME%%.*}" "${PWD/#$HOME/\~}"',
    )

    start_capturing()

    mock_pty_spawn.assert_called_once()
    assert terminal_log.exists()
    assert oct(terminal_log.stat().st_mode).endswith("600")


def test_terminal_recorder_can_initialize(tmp_path):
    dummy_file = tmp_path / "test.log"
    with dummy_file.open(mode="wb") as handler:
        instance = TerminalRecorder(handler)
        assert instance._handler == handler


def test_terminal_recorder_write_json_block(tmp_path):
    dummy_file = tmp_path / "test.log"
    with dummy_file.open(mode="wb") as handler:
        instance = TerminalRecorder(handler)
        assert instance._handler == handler

        instance._current_command = b"test"
        instance._current_output = b"test"

        instance.write_json_block()

    block = json.loads(dummy_file.read_text())
    assert block
    assert block["command"] == "test"
    assert block["output"] == "test"


@pytest.mark.parametrize(
    ("data", "expected"),
    (
        (b"test", b"test"),
        (b"test%c", b"test"),
        (b"test\n\r", b"test\n\r"),
    ),
)
def test_terminal_recorder_read(data, expected, monkeypatch, tmp_path):
    dummy_file = tmp_path / "test.log"
    monkeypatch.setattr(os, "read", mock.Mock(return_value=data))
    with dummy_file.open(mode="wb") as handler:
        instance = TerminalRecorder(handler)
        assert instance._handler == handler

        assert instance.read(0) == expected


@pytest.mark.parametrize(
    ("data", "expected"), ((b"test", b"test"), (b"test%c", b"test"))
)
def test_terminal_recorder_read_in_command_false(data, expected, monkeypatch, tmp_path):
    dummy_file = tmp_path / "test.log"
    monkeypatch.setattr(os, "read", mock.Mock(return_value=data))
    with dummy_file.open(mode="wb") as handler:
        instance = TerminalRecorder(handler)
        instance._in_command = False
        assert instance._handler == handler

        assert instance.read(0) == expected
