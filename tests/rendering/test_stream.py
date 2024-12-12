import sys

import pytest

from command_line_assistant.rendering.stream import StderrStream, StdoutStream


class TestStdoutStream:
    def test_initialization_default(self):
        """Test StdoutStream initialization with default end character"""
        stream = StdoutStream()
        assert stream._stream == sys.stdout
        assert stream._end == "\n"

    def test_initialization_custom_end(self):
        """Test StdoutStream initialization with custom end character"""
        stream = StdoutStream(end=">>>")
        assert stream._stream == sys.stdout
        assert stream._end == ">>>"

    def test_write(self, capsys):
        """Test writing to stdout"""
        stream = StdoutStream()
        test_message = "Hello, World!"
        stream.write(test_message)

        captured = capsys.readouterr()
        assert captured.out == f"{test_message}\n"

    def test_write_custom_end(self, capsys):
        """Test writing to stdout with custom end character"""
        stream = StdoutStream(end=">>>")
        test_message = "Hello, World!"
        stream.write(test_message)

        captured = capsys.readouterr()
        assert captured.out == f"{test_message}>>>"

    def test_write_empty_string(self, capsys):
        """Test writing empty string to stdout"""
        stream = StdoutStream()
        stream.write("")

        captured = capsys.readouterr()
        assert captured.out == "\n"

    def test_write_multiple_lines(self, capsys):
        """Test writing multiple lines to stdout"""
        stream = StdoutStream()
        messages = ["Line 1", "Line 2", "Line 3"]

        for message in messages:
            stream.write(message)

        captured = capsys.readouterr()
        expected = "".join(f"{msg}\n" for msg in messages)
        assert captured.out == expected

    def test_flush(self, capsys):
        """Test flushing stdout"""
        stream = StdoutStream()
        stream.write("Test message")
        stream.flush()

        captured = capsys.readouterr()
        assert captured.out == "Test message\n"

    def test_execute(self, capsys):
        """Test execute method with stdout"""
        stream = StdoutStream()
        test_message = "Execute test"
        stream.execute(test_message)

        captured = capsys.readouterr()
        assert captured.out == f"{test_message}\n"

    def test_execute_empty_string(self, capsys):
        """Test execute method with empty string"""
        stream = StdoutStream()
        stream.execute("")

        captured = capsys.readouterr()
        assert captured.out == ""


class TestStderrStream:
    def test_initialization_default(self):
        """Test StderrStream initialization with default end character"""
        stream = StderrStream()
        assert stream._stream == sys.stderr
        assert stream._end == "\n"

    def test_initialization_custom_end(self):
        """Test StderrStream initialization with custom end character"""
        stream = StderrStream(end="!!!")
        assert stream._stream == sys.stderr
        assert stream._end == "!!!"

    def test_write(self, capsys):
        """Test writing to stderr"""
        stream = StderrStream()
        test_message = "Error message"
        stream.write(test_message)

        captured = capsys.readouterr()
        assert captured.err == f"{test_message}\n"

    def test_write_custom_end(self, capsys):
        """Test writing to stderr with custom end character"""
        stream = StderrStream(end="!!!")
        test_message = "Error message"
        stream.write(test_message)

        captured = capsys.readouterr()
        assert captured.err == f"{test_message}!!!"

    def test_write_empty_string(self, capsys):
        """Test writing empty string to stderr"""
        stream = StderrStream()
        stream.write("")

        captured = capsys.readouterr()
        assert captured.err == "\n"

    def test_write_multiple_lines(self, capsys):
        """Test writing multiple lines to stderr"""
        stream = StderrStream()
        messages = ["Error 1", "Error 2", "Error 3"]

        for message in messages:
            stream.write(message)

        captured = capsys.readouterr()
        expected = "".join(f"{msg}\n" for msg in messages)
        assert captured.err == expected

    def test_flush(self, capsys):
        """Test flushing stderr"""
        stream = StderrStream()
        stream.write("Error message")
        stream.flush()

        captured = capsys.readouterr()
        assert captured.err == "Error message\n"

    def test_execute(self, capsys):
        """Test execute method with stderr"""
        stream = StderrStream()
        test_message = "Execute error test"
        stream.execute(test_message)

        captured = capsys.readouterr()
        assert captured.err == f"{test_message}\n"

    def test_execute_empty_string(self, capsys):
        """Test execute method with empty string"""
        stream = StderrStream()
        stream.execute("")

        captured = capsys.readouterr()
        assert captured.err == ""


@pytest.mark.parametrize(
    "StreamClass,expected_stream",
    [
        (StdoutStream, sys.stdout),
        (StderrStream, sys.stderr),
    ],
)
def test_stream_initialization(StreamClass, expected_stream):
    """Test initialization of both stream classes"""
    stream = StreamClass()
    assert stream._stream == expected_stream


@pytest.mark.parametrize("StreamClass", [StdoutStream, StderrStream])
def test_stream_unicode(StreamClass, capsys):
    """Test handling of Unicode characters in both streams"""
    stream = StreamClass()

    unicode_messages = [
        "Hello, 世界!",  # Japanese
        "¡Hola, món!",  # Catalan with Spanish punctuation
        "🌟 Stars ✨",  # Emojis
        "θ, π, φ",  # Greek letters
    ]

    for message in unicode_messages:
        stream.write(message)
        captured = capsys.readouterr()
        output = captured.out if isinstance(stream, StdoutStream) else captured.err
        assert message in output


@pytest.mark.parametrize("StreamClass", [StdoutStream, StderrStream])
def test_stream_long_messages(StreamClass, capsys):
    """Test handling of long messages in both streams"""
    stream = StreamClass()

    long_message = "x" * 10000  # 10K characters
    stream.write(long_message)

    captured = capsys.readouterr()
    output = captured.out if isinstance(stream, StdoutStream) else captured.err
    assert output.strip() == long_message


@pytest.mark.parametrize("StreamClass", [StdoutStream, StderrStream])
def test_stream_special_characters(StreamClass, capsys):
    """Test handling of special characters in both streams"""
    stream = StreamClass()

    special_messages = [
        "Tab\there",
        "New\nline",
        "Return\rchar",
        "Back\\slash",
        '"Quotes"',
    ]

    for message in special_messages:
        stream.write(message)
        captured = capsys.readouterr()
        output = captured.out if isinstance(stream, StdoutStream) else captured.err
        assert message in output
