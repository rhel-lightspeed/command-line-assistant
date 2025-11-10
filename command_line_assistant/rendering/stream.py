"""Module to hold the stream classes."""

import sys
from typing import Optional, TextIO

from command_line_assistant.rendering.markdown import markdown_to_ansi
from command_line_assistant.rendering.theme import Theme


class StreamWriter:
    """
    StreamWriter is a class that writes receives chunks of markdown text
    and renders them as ANSI formatted text before writing them to a stream. If
    a chunk cannot be rendered as ANSI formatted text, it is cached in a buffer
    and prepended to the next chunk.
    """

    def __init__(
        self,
        stream: TextIO = sys.stdout,
        flush_on_write: bool = True,
        theme: Optional[Theme] = None,
    ):
        """
        Initialize the StreamWriter.

        Args:
            stream: Output stream to write to. Defaults to sys.stdout.
            flush_on_write: Whether to flush the stream after each successful
            write. Defaults to True.
        """
        self._stream = stream
        self._buffer = ""
        self._flush_on_write = flush_on_write
        self._theme = theme or Theme()

    def write_line(self, line: str) -> None:
        """Write a line of unformatted text to the stream."""
        self._stream.write(line + "\n")
        if self._flush_on_write:
            self._stream.flush()

    def write_markdown_chunk(self, chunk: str) -> None:
        """
        Write a chunk of markdown text to the stream.

        If the chunk cannot be rendered as ANSI formatted text, it is cached in
        the buffer and prepended to the next chunk for retry.

        Args:
            chunk: A piece of markdown content to format and write.
        """
        if not chunk:
            return

        # Combine buffered content with new chunk
        content_to_render = self._buffer + chunk

        try:
            # Try to render the combined content as markdown
            formatted_content = markdown_to_ansi(content_to_render, theme=self._theme)

            # If successful, write to stream and clear buffer
            self.write_line(formatted_content)
            self._buffer = ""

            if self._flush_on_write:
                self._stream.flush()

        except Exception:
            # If rendering fails, store the content in buffer for next attempt
            self._buffer = content_to_render

    def flush(self) -> None:
        """
        Flush any remaining buffered content to the stream.

        This method attempts to render any buffered markdown content. If
        rendering fails, the content is written as-is to the stream.
        """
        if self._buffer:
            try:
                # Try to render buffered content one final time
                formatted_content = markdown_to_ansi(self._buffer, theme=self._theme)
                self._stream.write(formatted_content)
            except Exception:
                # If rendering still fails, write raw content
                self._stream.write(self._buffer)

            # Clear the buffer
            self._buffer = ""

        # Flush the underlying stream
        self._stream.flush()

    def close(self) -> None:
        """
        Flush any remaining content and close the stream.

        This method ensures all buffered content is written before closing.
        """
        self.flush()

        # Close the stream if it has a close method
        if hasattr(self._stream, "close"):
            self._stream.close()
