import sys

from command_line_assistant.rendering.base import (
    OutputStreamWritter,
)


class StderrStream(OutputStreamWritter):
    """Decorator for outputting text to stderr"""

    def __init__(self, end: str = "\n") -> None:
        """
        Initialize the stderr decorator.

        Args:
            end: The string to append after the text (defaults to newline)
        """
        super().__init__(stream=sys.stderr, end=end)

    def write(self, text: str) -> None:
        """Write the text to stderr"""
        self._stream.write(text + self._end)

    def flush(self) -> None:
        """Flush stderr"""
        self._stream.flush()


class StdoutStream(OutputStreamWritter):
    """Decorator for outputting text to stdout"""

    def __init__(self, end: str = "\n") -> None:
        """
        Initialize the stdout decorator.

        Args:
            end: The string to append after the text (defaults to newline)
        """
        super().__init__(stream=sys.stdout, end=end)

    def write(self, text: str) -> None:
        """Write the text to stdout"""
        self._stream.write(text + self._end)

    def flush(self) -> None:
        """Flush stdout"""
        self._stream.flush()
