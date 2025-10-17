"""Utility module that provides standardized functions for rendering"""

from datetime import datetime
from typing import Optional

from command_line_assistant.rendering.colors import colorize
from command_line_assistant.rendering.stream import StreamWriter
from command_line_assistant.rendering.theme import Theme


def human_readable_size(size: float) -> str:
    """Converts a byte value to a human-readable format (KB, MB, GB).

    Arguments:
        size (float): The size to be converted to a human readable format

    Returns:
        str: Size in a human readable format
    """
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0

    while size >= 1000 and unit_index < len(units) - 1:
        size /= 1000
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


def format_datetime(unformatted_date: str) -> str:
    """Format a datetime string to a more human readable format.

    Arguments:
        unformatted_date (str): The unformatted date (usually, it is datetime.now())

    Returns:
        str: The formatted date in human readable time.
    """
    # Convert str to datetime object
    date = datetime.strptime(unformatted_date, "%Y-%m-%d %H:%M:%S.%f")
    return date.strftime("%A, %B %d, %Y at %I:%M:%S %p")


class Renderer:
    """Renderer provides methods for rendering text using different, predefined
    colors and styles.
    """

    def __init__(self, plain: bool = False, theme: Optional[Theme] = None):
        """Initialize render utilities.

        Args:
            plain (bool): Whether to use plain text rendering
            theme (Theme): Theme instance to use for colors. If None, uses
            default theme.
        """
        self._plain = plain
        self._stream_writer: StreamWriter = StreamWriter(theme=theme)
        self._theme = theme or Theme()

    def normal(self, message: str) -> None:
        """Render a message with a normal color.

        Args:
            message (str): Text to render
        """
        self._stream_writer.write_line(message)

    def warning(self, message: str) -> None:
        """Render a message with a yellow color.

        Args:
            message: Text to render
        """
        if self._plain:
            self._stream_writer.write_line(message)
        else:
            self._stream_writer.write_line(
                "🤔 " + colorize(message, self._theme.warning)
            )

    def notice(self, message: str) -> None:
        """Render a message with a bright yellow color.

        Args:
            message: Text to render
        """
        if self._plain:
            self._stream_writer.write_line(message)
        else:
            self._stream_writer.write_line(colorize(message, self._theme.notice))

    def info(self, message: str) -> None:
        """Render a message with a bright blue color.

        Args:
            message: Text to render
        """
        if self._plain:
            self._stream_writer.write_line(message)
        else:
            self._stream_writer.write_line(colorize(message, self._theme.info))

    def error(self, message: str) -> None:
        """Render a message with a red color.

        Args:
            message: Text to render
        """
        if self._plain:
            self._stream_writer.write_line(message)
        else:
            self._stream_writer.write_line("🙁 " + colorize(message, self._theme.error))

    def markdown(self, message: str) -> None:
        """Render markdown formatted text.

        Args:
            message: Text to render
        """
        if self._plain:
            self._stream_writer.write_line(message)
        else:
            self._stream_writer.write_markdown_chunk(message)
