import io
import sys
from unittest.mock import Mock, patch

import pytest

from command_line_assistant.rendering.stream import StreamWriter


@pytest.fixture
def disable_stream_flush(monkeypatch):
    """Fixture to make StreamWriter use current sys.stdout and disable flushing."""
    import sys

    from command_line_assistant.rendering.stream import StreamWriter

    # Patch StreamWriter to use current sys.stdout and disable flushing
    original_init = StreamWriter.__init__

    def patched_init(self, stream=None, flush_on_write=True, theme=None):
        # Always use current sys.stdout and disable flushing
        original_init(self, stream=sys.stdout, flush_on_write=False, theme=theme)

    monkeypatch.setattr(StreamWriter, "__init__", patched_init)
    yield


class TestStreamWriter:
    def test_write_chunk(self, capsys, disable_stream_flush):
        stream = StreamWriter()
        stream.write_chunk("Hello, world!")
        assert capsys.readouterr().out == "Hello, world!"

    def test_init_default_parameters(self):
        """Test StreamWriter initialization with default parameters."""
        stream = StreamWriter()
        assert stream._stream is sys.stdout
        assert stream._flush_on_write is True
        assert stream._buffer == ""

    def test_init_all_custom_parameters(self):
        """Test StreamWriter initialization with all custom parameters."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream, flush_on_write=False)
        assert stream._stream is custom_stream
        assert stream._flush_on_write is False
        assert stream._buffer == ""

    def test_write_line_basic(self):
        """Test write_line method with basic string."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_line("Hello, world!")

        assert custom_stream.getvalue() == "Hello, world!\n"

    def test_write_line_empty_string(self):
        """Test write_line method with empty string."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_line("")

        assert custom_stream.getvalue() == "\n"

    def test_write_line_multiline_input(self):
        """Test write_line method with multiline input."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_line("Line 1\nLine 2")

        assert custom_stream.getvalue() == "Line 1\nLine 2\n"

    def test_write_line_with_flush_disabled(self):
        """Test write_line method with flush disabled."""
        mock_stream = Mock()
        stream = StreamWriter(stream=mock_stream, flush_on_write=False)

        stream.write_line("Test line")

        mock_stream.write.assert_called_once_with("Test line\n")
        mock_stream.flush.assert_not_called()

    def test_write_line_with_flush_enabled(self):
        """Test write_line method with flush enabled."""
        mock_stream = Mock()
        stream = StreamWriter(stream=mock_stream, flush_on_write=True)

        stream.write_line("Test line")

        mock_stream.write.assert_called_once_with("Test line\n")
        mock_stream.flush.assert_called_once()

    def test_write_chunk_with_flush_disabled(self):
        """Test write_chunk method with flush disabled."""
        mock_stream = Mock()
        stream = StreamWriter(stream=mock_stream, flush_on_write=False)

        stream.write_chunk("Test chunk")

        mock_stream.write.assert_called_once_with("Test chunk")
        mock_stream.flush.assert_not_called()

    def test_write_chunk_with_flush_enabled(self):
        """Test write_chunk method with flush enabled."""
        mock_stream = Mock()
        stream = StreamWriter(stream=mock_stream, flush_on_write=True)

        stream.write_chunk("Test chunk")

        mock_stream.write.assert_called_once_with("Test chunk")
        mock_stream.flush.assert_called_once()

    def test_write_chunk_empty_string(self):
        """Test write_chunk method with empty string."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_chunk("")

        assert custom_stream.getvalue() == ""

    def test_write_markdown_chunk_empty_string(self):
        """Test write_markdown_chunk method with empty string."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_markdown_chunk("")

        assert custom_stream.getvalue() == ""
        assert stream._buffer == ""

    def test_write_markdown_chunk_valid_markdown(self):
        """Test write_markdown_chunk method with valid markdown."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_markdown_chunk("**Bold text**")

        # Should render and write to stream
        output = custom_stream.getvalue()
        assert output != ""  # Should contain ANSI formatted text
        assert stream._buffer == ""  # Buffer should be cleared after successful render

    def test_write_markdown_chunk_simple_text(self):
        """Test write_markdown_chunk method with simple text."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_markdown_chunk("Simple text")

        # Should render and write to stream
        output = custom_stream.getvalue()
        assert "Simple text" in output
        assert stream._buffer == ""  # Buffer should be cleared after successful render

    @patch("command_line_assistant.rendering.stream.markdown_to_ansi")
    def test_write_markdown_chunk_rendering_exception(self, mock_markdown_to_ansi):
        """Test write_markdown_chunk when markdown rendering raises an exception."""
        mock_markdown_to_ansi.side_effect = Exception("Rendering failed")

        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_markdown_chunk("Some markdown")

        # Should buffer the content when rendering fails
        assert stream._buffer == "Some markdown"
        assert custom_stream.getvalue() == ""  # Nothing written to stream
        mock_markdown_to_ansi.assert_called_once()
        args, kwargs = mock_markdown_to_ansi.call_args
        assert args[0] == "Some markdown"
        assert "theme" in kwargs

    @patch("command_line_assistant.rendering.stream.markdown_to_ansi")
    def test_write_markdown_chunk_buffering_accumulation(self, mock_markdown_to_ansi):
        """Test write_markdown_chunk accumulates content in buffer on repeated failures."""
        mock_markdown_to_ansi.side_effect = Exception("Rendering failed")

        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_markdown_chunk("First chunk")
        stream.write_markdown_chunk(" Second chunk")

        # Should accumulate content in buffer
        assert stream._buffer == "First chunk Second chunk"
        assert custom_stream.getvalue() == ""
        assert mock_markdown_to_ansi.call_count == 2

    @patch("command_line_assistant.rendering.stream.markdown_to_ansi")
    def test_write_markdown_chunk_buffer_recovery(self, mock_markdown_to_ansi):
        """Test write_markdown_chunk recovers from buffer when rendering succeeds."""
        # First call fails, second succeeds
        mock_markdown_to_ansi.side_effect = [
            Exception("Rendering failed"),
            "Formatted content",
        ]

        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        # First chunk fails and gets buffered
        stream.write_markdown_chunk("First chunk")
        assert stream._buffer == "First chunk"

        # Second chunk succeeds with buffered content
        stream.write_markdown_chunk(" Second chunk")

        # Should write formatted content and clear buffer
        assert custom_stream.getvalue() == "Formatted content"
        assert stream._buffer == ""

        # Should have called with combined content on second attempt
        assert mock_markdown_to_ansi.call_count == 2
        first_call_args = mock_markdown_to_ansi.call_args_list[0]
        second_call_args = mock_markdown_to_ansi.call_args_list[1]
        assert first_call_args[0][0] == "First chunk"
        assert second_call_args[0][0] == "First chunk Second chunk"
        assert "theme" in first_call_args[1]
        assert "theme" in second_call_args[1]

    def test_write_markdown_chunk_with_flush_disabled(self):
        """Test write_markdown_chunk with flush disabled."""
        mock_stream = Mock()
        stream = StreamWriter(stream=mock_stream, flush_on_write=False)

        stream.write_markdown_chunk("Simple text")

        # Should write but not flush
        mock_stream.write.assert_called_once()
        mock_stream.flush.assert_not_called()

    def test_write_markdown_chunk_with_flush_enabled(self):
        """Test write_markdown_chunk with flush enabled."""
        mock_stream = Mock()
        stream = StreamWriter(stream=mock_stream, flush_on_write=True)

        stream.write_markdown_chunk("Simple text")

        # Should write and flush
        mock_stream.write.assert_called_once()
        mock_stream.flush.assert_called_once()

    def test_flush_empty_buffer(self):
        """Test flush method with empty buffer."""
        mock_stream = Mock()
        stream = StreamWriter(stream=mock_stream)

        stream.flush()

        # Should only flush the stream, no writes
        mock_stream.write.assert_not_called()
        mock_stream.flush.assert_called_once()

    @patch("command_line_assistant.rendering.stream.markdown_to_ansi")
    def test_flush_with_buffered_content_success(self, mock_markdown_to_ansi):
        """Test flush method with buffered content that renders successfully."""
        mock_markdown_to_ansi.return_value = "Formatted content"

        mock_stream = Mock()
        stream = StreamWriter(stream=mock_stream)
        stream._buffer = "Buffered markdown"

        stream.flush()

        # Should render and write buffered content
        mock_markdown_to_ansi.assert_called_once()
        args, kwargs = mock_markdown_to_ansi.call_args
        assert args[0] == "Buffered markdown"
        assert "theme" in kwargs
        mock_stream.write.assert_called_once_with("Formatted content")
        mock_stream.flush.assert_called_once()
        assert stream._buffer == ""

    @patch("command_line_assistant.rendering.stream.markdown_to_ansi")
    def test_flush_with_buffered_content_failure(self, mock_markdown_to_ansi):
        """Test flush method with buffered content that fails to render."""
        mock_markdown_to_ansi.side_effect = Exception("Rendering failed")

        mock_stream = Mock()
        stream = StreamWriter(stream=mock_stream)
        stream._buffer = "Buffered markdown"

        stream.flush()

        # Should write raw content when rendering fails
        mock_markdown_to_ansi.assert_called_once()
        args, kwargs = mock_markdown_to_ansi.call_args
        assert args[0] == "Buffered markdown"
        assert "theme" in kwargs
        mock_stream.write.assert_called_once_with("Buffered markdown")
        mock_stream.flush.assert_called_once()
        assert stream._buffer == ""

    def test_flush_clears_buffer_regardless_of_outcome(self):
        """Test that flush always clears the buffer."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)
        stream._buffer = "Some content"

        stream.flush()

        # Buffer should be cleared even if content was written as raw
        assert stream._buffer == ""
        assert custom_stream.getvalue() == "Some content"

    def test_close_calls_flush(self):
        """Test that close method calls flush."""
        mock_stream = Mock()
        mock_stream.close = Mock()  # Add close method to mock

        stream = StreamWriter(stream=mock_stream)
        stream._buffer = "Some content"

        stream.close()

        # Should flush content and close stream
        mock_stream.write.assert_called_once_with("Some content")
        mock_stream.flush.assert_called_once()
        mock_stream.close.assert_called_once()
        assert stream._buffer == ""

    def test_close_with_stream_without_close_method(self):
        """Test close method with a stream that doesn't have close method."""
        # Create a mock without close method
        mock_stream = Mock(spec=["write", "flush"])

        stream = StreamWriter(stream=mock_stream)
        stream._buffer = "Some content"

        # Should not raise an error even if stream has no close method
        stream.close()

        # Should still flush content
        mock_stream.write.assert_called_once_with("Some content")
        mock_stream.flush.assert_called_once()
        assert stream._buffer == ""

    def test_close_with_empty_buffer(self):
        """Test close method with empty buffer."""
        mock_stream = Mock()
        mock_stream.close = Mock()

        stream = StreamWriter(stream=mock_stream)

        stream.close()

        # Should only flush and close, no writes
        mock_stream.write.assert_not_called()
        mock_stream.flush.assert_called_once()
        mock_stream.close.assert_called_once()

    def test_close_with_stringio(self):
        """Test close method with StringIO stream."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)
        stream._buffer = "Buffered content"

        stream.close()

        # Should flush content and close stream
        # Note: We check the buffer is cleared and stream is closed
        # We can't read from custom_stream.getvalue() after close() as the stream is closed
        assert stream._buffer == ""
        assert custom_stream.closed

    def test_multiple_write_operations_sequence(self):
        """Test a sequence of different write operations."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        # Mix of different write methods
        stream.write_chunk("Chunk 1 ")
        stream.write_line("Line 1")
        stream.write_markdown_chunk("**Bold text** ")
        stream.write_chunk("Final chunk")

        output = custom_stream.getvalue()
        assert "Chunk 1 " in output
        assert "Line 1\n" in output
        assert "Final chunk" in output
        # Bold text should be rendered with ANSI codes
        assert output != "Chunk 1 Line 1\n**Bold text** Final chunk"

    def test_write_markdown_chunk_with_newlines(self):
        """Test write_markdown_chunk with content containing newlines."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_markdown_chunk("Line 1\n**Bold Line 2**\nLine 3")

        output = custom_stream.getvalue()
        assert "Line 1" in output
        assert "Line 3" in output
        assert stream._buffer == ""

    def test_write_chunk_with_special_characters(self):
        """Test write_chunk with special characters and unicode."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        special_text = "Special chars: !@#$%^&*() Unicode: 🚀 ñoño"
        stream.write_chunk(special_text)

        assert custom_stream.getvalue() == special_text

    def test_buffer_state_isolation(self):
        """Test that buffer state is isolated between instances."""
        stream1 = StreamWriter(stream=io.StringIO())
        stream2 = StreamWriter(stream=io.StringIO())

        stream1._buffer = "Buffer 1"
        stream2._buffer = "Buffer 2"

        assert stream1._buffer == "Buffer 1"
        assert stream2._buffer == "Buffer 2"

    @patch("command_line_assistant.rendering.stream.markdown_to_ansi")
    def test_write_markdown_chunk_with_none_input(self, mock_markdown_to_ansi):
        """Test write_markdown_chunk behavior with None input (edge case)."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        # This would normally cause a TypeError, but let's test graceful handling
        try:
            stream.write_markdown_chunk(None)  # type: ignore
        except (TypeError, AttributeError):
            # Expected behavior - the method should handle string operations
            pass

        # Ensure no calls were made to markdown processing if None was passed
        mock_markdown_to_ansi.assert_not_called()

    def test_large_content_handling(self):
        """Test handling of large content chunks."""
        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        # Create a large chunk of content
        large_content = "A" * 10000
        stream.write_chunk(large_content)

        assert custom_stream.getvalue() == large_content
        assert len(custom_stream.getvalue()) == 10000

    @patch("command_line_assistant.rendering.stream.markdown_to_ansi")
    def test_consecutive_markdown_failures_and_success(self, mock_markdown_to_ansi):
        """Test multiple consecutive markdown failures followed by success."""
        # Fail twice, then succeed
        mock_markdown_to_ansi.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            "Success!",
        ]

        custom_stream = io.StringIO()
        stream = StreamWriter(stream=custom_stream)

        stream.write_markdown_chunk("chunk1")
        stream.write_markdown_chunk("chunk2")
        stream.write_markdown_chunk("chunk3")

        # Should have accumulated all chunks and then rendered successfully
        assert custom_stream.getvalue() == "Success!"
        assert stream._buffer == ""
        assert mock_markdown_to_ansi.call_count == 3
