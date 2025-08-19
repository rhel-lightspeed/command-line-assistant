"""Streaming output classes for real-time markdown rendering to stdout."""

import sys
from typing import TextIO

from command_line_assistant.rendering.markdown import markdown_to_ansi


class MarkdownStreamer:
    """
    A class that streams chunked markdown content to stdout with ANSI formatting.

    This class accumulates markdown chunks and renders them in real-time to stdout
    using the ANSI markdown formatter. It handles partial markdown content gracefully
    and ensures proper formatting even when chunks arrive incrementally.
    """

    def __init__(self, stream: TextIO = sys.stdout, flush_on_chunk: bool = True):
        """
        Initialize the markdown streamer.

        Args:
            stream: Output stream to write to. Defaults to sys.stdout.
            flush_on_chunk: Whether to flush the stream after each chunk. Defaults to True.
        """
        self._stream = stream
        self._buffer = ""
        self._flush_on_chunk = flush_on_chunk

    def add_chunk(self, chunk: str) -> None:
        """
        Add a chunk of markdown content with immediate ANSI formatting.

        Args:
            chunk: A piece of markdown content to format and output immediately.
        """
        if not chunk:
            return

        # Try to format the chunk as markdown immediately
        try:
            formatted_chunk = markdown_to_ansi(chunk)
            self._stream.write(formatted_chunk)
        except Exception:
            # If formatting fails, write raw chunk
            self._stream.write(chunk)

        if self._flush_on_chunk:
            self._stream.flush()

    def add_formatted_chunk(self, chunk: str) -> None:
        """
        Add a pre-formatted chunk directly to the stream.

        Args:
            chunk: Pre-formatted content to write directly.
        """
        if chunk:
            self._stream.write(chunk)
            if self._flush_on_chunk:
                self._stream.flush()

    def add_line_chunk(self, chunk: str) -> None:
        """
        Add a chunk of markdown content as a complete line and render it.

        This method is useful when you want to render complete lines of markdown
        as they arrive, rather than accumulating in a buffer.

        Args:
            chunk: A line or chunk of markdown content to render immediately.
        """
        if not chunk:
            return

        try:
            formatted_text = markdown_to_ansi(chunk)
            self._stream.write(formatted_text + "\n")

            if self._flush_on_chunk:
                self._stream.flush()

        except Exception:
            # If markdown parsing fails, write raw chunk
            self._stream.write(chunk)
            if self._flush_on_chunk:
                self._stream.flush()

    def finalize(self) -> None:
        """
        Finalize the streaming output and ensure all content is properly rendered.

        This method should be called when all chunks have been added to ensure
        the final output is properly formatted and flushed.
        """
        if self._buffer:
            try:
                final_formatted = markdown_to_ansi(self._buffer)
                self._stream.write("\r\033[K")  # Clear current line
                self._stream.write(final_formatted)
                self._stream.write("\n")  # Add final newline
            except Exception:
                self._stream.write(self._buffer)
                self._stream.write("\n")

        self._stream.flush()
        self._buffer = ""

    def clear_buffer(self) -> None:
        """Clear the internal buffer without rendering."""
        self._buffer = ""

    def get_buffer(self) -> str:
        """Get the current buffer content."""
        return self._buffer

    def write_raw(self, text: str) -> None:
        """
        Write raw text to the stream without markdown formatting.

        Args:
            text: Raw text to write to the stream.
        """
        self._stream.write(text)
        if self._flush_on_chunk:
            self._stream.flush()


class ProgressiveMarkdownStreamer(MarkdownStreamer):
    """
    Enhanced markdown streamer that handles progressive rendering with better
    handling of incomplete markdown structures.

    This class is designed for scenarios where markdown content arrives in small
    chunks and you want to show progressive updates while maintaining proper formatting.
    """

    def __init__(
        self,
        stream: TextIO = sys.stdout,
        flush_on_chunk: bool = True,
        min_chunk_size: int = 50,
    ):
        """
        Initialize the progressive markdown streamer.

        Args:
            stream: Output stream to write to. Defaults to sys.stdout.
            flush_on_chunk: Whether to flush the stream after each chunk.
            min_chunk_size: Minimum buffer size before attempting to render.
        """
        super().__init__(stream, flush_on_chunk)
        self._min_chunk_size = min_chunk_size
        self._last_rendered_length = 0

    def add_chunk(self, chunk: str) -> None:
        """
        Add a chunk with progressive rendering logic.

        Only renders when buffer reaches minimum size or contains complete markdown elements.

        Args:
            chunk: A piece of markdown content to add.
        """
        if not chunk:
            return

        self._buffer += chunk

        # Only render if we have enough content or if we detect complete markdown elements
        should_render = (
            len(self._buffer) >= self._min_chunk_size
            or self._has_complete_elements(chunk)
            or chunk.endswith("\n")
        )

        if should_render:
            self._render_progressive()

    def _has_complete_elements(self, chunk: str) -> bool:
        """
        Check if the chunk contains complete markdown elements.

        Args:
            chunk: The chunk to check.

        Returns:
            True if the chunk likely contains complete markdown elements.
        """
        # Check for complete markdown elements
        complete_indicators = [
            "\n\n",  # Paragraph break
            "```\n",  # End of code block
            "\n#",  # Header
            "\n-",  # List item
            "\n*",  # List item or emphasis
            "\n>",  # Blockquote
        ]

        return any(indicator in chunk for indicator in complete_indicators)

    def _render_progressive(self) -> None:
        """Render the current buffer progressively."""
        try:
            formatted_text = markdown_to_ansi(self._buffer)

            # Calculate what's new since last render
            new_content = formatted_text[self._last_rendered_length :]

            if new_content:
                self._stream.write(new_content)
                self._last_rendered_length = len(formatted_text)

                if self._flush_on_chunk:
                    self._stream.flush()

        except Exception:
            # If formatting fails, just write the new raw content
            new_raw_content = self._buffer[self._last_rendered_length :]
            if new_raw_content:
                self._stream.write(new_raw_content)
                self._last_rendered_length = len(self._buffer)

                if self._flush_on_chunk:
                    self._stream.flush()

    def finalize(self) -> None:
        """Finalize with progressive rendering reset."""
        super().finalize()
        self._last_rendered_length = 0
