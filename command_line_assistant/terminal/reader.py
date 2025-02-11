"""Module to hold the reader part of the terminal module."""

import json
import os
import pty
from pathlib import Path
from typing import IO

from typing_extensions import Any

from command_line_assistant.utils.environment import get_xdg_state_path
from command_line_assistant.utils.files import create_folder, write_file

#: Special prompt marker to help us figure out when we should capture a new command/output.
PROMPT_MARKER: str = "%c"

#: The name of the output file to store the logs.
OUTPUT_FILE_NAME: Path = Path(get_xdg_state_path(), "terminal.log")


class TerminalRecorder:
    """Class that controls how the terminal is being read"""

    def __init__(self, handler: IO[Any]) -> None:
        """Constructor of the class.

        Arguments:
            handler (IO[Any]): The file handler opened during the screen reader.
        """
        self._handler = handler
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
        data = os.read(fd, 1024)

        if self._prompt_marker in data:
            if not self._in_command:
                self.write_json_block()
            self._in_command = True
        elif self._in_command and (b"\r\n" in data or b"\n" in data):
            self._in_command = False

        # Remove our marker from the output
        data = data.replace(self._prompt_marker, b"")

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
    # Read our special environment variable to get the PROMPT_COMMAND, in case
    # it does not exists, set a default PROMPT_COMMAND for it.
    user_prompt_command = os.environ.get("CLA_USER_SHELL_PROMPT_COMMAND", r"")

    # Modify PROMPT_COMMAND and PS1 to include our marker
    os.environ["PROMPT_COMMAND"] = f"{user_prompt_command}{PROMPT_MARKER}"

    # Get the current user SHELL environment variable, if not set, use sh.
    shell = os.environ.get("SHELL", "/usr/bin/sh")

    # Set up proper shell environment variables for job control
    os.environ["TERM"] = os.environ.get("TERM", "xterm")

    # The create_folder function will silently fail in case the folder exists.
    create_folder(OUTPUT_FILE_NAME.parent)

    # Initialize the file
    write_file("", OUTPUT_FILE_NAME)

    with OUTPUT_FILE_NAME.open(mode="wb") as handler:
        # Instantiate the TerminalRecorder and spawn a new shell with pty.
        recorder = TerminalRecorder(handler)
        pty.spawn([shell, "-i"], recorder.read)

        # Write the final json block if it exists.
        recorder.write_json_block()
