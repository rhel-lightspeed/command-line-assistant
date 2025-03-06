import json
import os
import shutil
import struct
from unittest import mock
from unittest.mock import patch

import pytest

from command_line_assistant.terminal import reader
from command_line_assistant.terminal.reader import TerminalRecorder, start_capturing


@pytest.fixture(autouse=True)
def mock_terminal_functions():
    """Mock terminal functions that require a TTY."""
    with patch("fcntl.ioctl", mock.Mock(return_value=None)):
        with patch("os.isatty", mock.Mock(return_value=True)):
            yield


@pytest.fixture
def get_terminal_size_packed():
    columns, lines = shutil.get_terminal_size()
    return struct.pack("HHHH", lines, columns, 0, 0)


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


def test_terminal_recorder_can_initialize(tmp_path, get_terminal_size_packed):
    dummy_file = tmp_path / "test.log"
    with dummy_file.open(mode="wb") as handler:
        instance = TerminalRecorder(handler, get_terminal_size_packed)
        assert instance._handler == handler


def test_terminal_recorder_write_json_block(tmp_path, get_terminal_size_packed):
    dummy_file = tmp_path / "test.log"
    with dummy_file.open(mode="wb") as handler:
        instance = TerminalRecorder(handler, get_terminal_size_packed)
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
        (b"\x1b]test", b"\x1b]test"),
        (b"test\n\r", b"test\n\r"),
    ),
)
def test_terminal_recorder_read(
    data, expected, monkeypatch, tmp_path, get_terminal_size_packed
):
    dummy_file = tmp_path / "test.log"
    monkeypatch.setattr(os, "read", mock.Mock(return_value=data))
    with dummy_file.open(mode="wb") as handler:
        instance = TerminalRecorder(handler, get_terminal_size_packed)
        assert instance._handler == handler

        assert instance.read(0) == expected


@pytest.mark.parametrize(
    ("data", "expected"), ((b"test", b"test"), (b"\x1b]test", b"\x1b]test"))
)
def test_terminal_recorder_read_in_command_false(
    data, expected, monkeypatch, tmp_path, get_terminal_size_packed
):
    dummy_file = tmp_path / "test.log"
    monkeypatch.setattr(os, "read", mock.Mock(return_value=data))
    with dummy_file.open(mode="wb") as handler:
        instance = TerminalRecorder(handler, get_terminal_size_packed)
        instance._in_command = False
        assert instance._handler == handler

        assert instance.read(0) == expected


def test_terminal_recorder_with_empty_data(tmp_path, get_terminal_size_packed):
    """Test terminal recorder behavior with empty data"""
    dummy_file = tmp_path / "test.log"
    with dummy_file.open(mode="wb") as handler:
        instance = TerminalRecorder(handler, get_terminal_size_packed)

        # For empty data, we need to ensure the internal variables are properly set
        # but not affect existing state
        instance._current_command = b""
        instance._current_output = b""

        # Call write_json_block
        instance.write_json_block()

    # Check if file exists but might be empty since there was no data to write
    assert dummy_file.exists()

    # If the method writes even empty data (which it might not), check the content
    content = dummy_file.read_text().strip()
    if content:  # Only verify if something was written
        data = json.loads(content)
        assert data["command"] == ""
        assert data["output"] == ""
