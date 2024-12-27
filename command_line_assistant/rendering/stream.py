"""Module to hold the stream classes."""

import sys

from command_line_assistant.rendering.base import (
    BaseStream,
)


class StderrStream(BaseStream):
    """Decorator for outputting text to stderr"""

    def __init__(self, end: str = "\n") -> None:
        """Constructor of class.

        Args:
            end (str): The string to append after the text. Defaults to "\n".
        """
        super().__init__(stream=sys.stderr, end=end)


class StdoutStream(BaseStream):
    """Decorator for outputting text to stdout"""

    def __init__(self, end: str = "\n") -> None:
        """Constructor of class.

        Args:
            end (str): The string to append after the text. Defaults to "\n".
        """
        super().__init__(stream=sys.stdout, end=end)
