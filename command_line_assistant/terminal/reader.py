"""Module to hold the reader part of the terminal module."""

import fcntl
import json
import logging
import os
import pty
import shutil
import struct
import termios
from pathlib import Path
from typing import IO, Any

from command_line_assistant.utils.environment import get_xdg_state_path
from command_line_assistant.utils.files import create_folder, write_file

#: Special prompt marker to help us figure out when we should capture a new command/output.
PROMPT_MARKER: str = "\x1b]"

#: The name of the output file to store the logs.
OUTPUT_FILE_NAME: Path = Path(get_xdg_state_path(), "terminal.log")

logger = logging.getLogger(__name__)


class TerminalRecorder:
    """Class that controls how the terminal is being read"""

    def __init__(self, handler: IO[Any], winsize: bytes) -> None:
        """Constructor of the class.

        Arguments:
            handler (IO[Any]): The file handler opened during the screen reader.
            winsize (bytes): A packed struct with the original terminal size.
        """
        self._handler = handler
        self._winsize = winsize

        self._in_command: bool = True
        self._current_command: bytes = b""
        self._current_output: bytes = b""
        self._prompt_marker: bytes = PROMPT_MARKER.encode()

    def write_json_block(self):
        """Write a json block to the file once it's read."""
        if self._current_command:
            block = {
                "command": self._current_command.decode().strip(),
                "output": self._current_output.decode().strip(),
            }
            self._handler.write(json.dumps(block).encode() + b"\n")
            self._handler.flush()
            self._current_command = b""
            self._current_output = b""

    def read(self, fd: int) -> bytes:
        """Callback method that is used to read data from pty.

        Arguments:
            fd (int): File description used in read operation

        Returns:
            bytes: The data read from the terminal
        """
        fcntl.ioctl(fd, termios.TIOCSWINSZ, self._winsize)

        data = os.read(fd, 1024)
        if data.startswith(self._prompt_marker):
            if not self._in_command:
                self.write_json_block()
            self._in_command = True
        elif self._in_command and (b"\r\n" in data or b"\n" in data):
            self._in_command = False

        # Store command or output
        if self._in_command:
            self._current_command += data
        else:
            self._current_output += data

        return data


def start_capturing() -> None:
    """Routine to start capturing the terminal output and store it in a file.

    Note:
        This routine will capture every single piece of information that is
        displayed on the terminal as soon as it is enabled.

        Currently, we only support `bash` as our shell. The reason for that is
        that we need to inject a specific marker in the `PROMPT_COMMAND` and
        `PS1` to reliably capture the output. The marker can be seen in the
        global constant of this module `py:PROMPT_MARKER`.

        The log is stored under $XDG_STATE_HOME/command-line-assistant/terminal.log,
        if the user specify a path for $XDG_STATE_HOME, we use it, otherwise,
        we default to `~/.local/state` folder.
    """
    # Get the current user SHELL environment variable, if not set, use sh.
    shell = os.environ.get("SHELL", "/usr/bin/sh")

    # The create_folder function will silently fail in case the folder exists.
    create_folder(OUTPUT_FILE_NAME.parent, parents=True)

    # Initialize the file
    write_file("", OUTPUT_FILE_NAME)

    columns, lines = shutil.get_terminal_size()
    logger.debug(
        "Got terminal size of %sx%s (columns=%s, lines=%s).",
        columns,
        lines,
        columns,
        lines,
    )

    with OUTPUT_FILE_NAME.open(mode="wb") as handler:
        recorder = TerminalRecorder(handler, struct.pack("HHHH", lines, columns, 0, 0))

        # Instantiate the TerminalRecorder and spawn a new shell with pty.
        pty.spawn([shell], recorder.read)

        # Write the final json block if it exists.
        recorder.write_json_block()
