import threading
import time
from unittest.mock import MagicMock

import pytest

from command_line_assistant.rendering.base import OutputStreamWritter
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
    TextWrapDecorator,
)
from command_line_assistant.rendering.renders.spinner import Frames, SpinnerRenderer


class MockStream(OutputStreamWritter):
    """Mock stream class for testing"""

    def __init__(self):
        self.written = []
        super().__init__(stream=MagicMock())

    def write(self, text: str) -> None:
        self.written.append(text)

    def flush(self) -> None:
        pass


@pytest.fixture
def mock_stream():
    return MockStream()


@pytest.fixture
def spinner(mock_stream):
    return SpinnerRenderer("Loading...", stream=mock_stream)


def test_spinner_initialization():
    """Test spinner initialization with default values"""
    spinner = SpinnerRenderer("Loading...")
    assert spinner._message == "Loading..."
    assert spinner._delay == 0.1
    assert spinner._clear_message is False
    assert spinner._done.is_set() is False
    assert spinner._spinner_thread is None


def test_spinner_custom_initialization():
    """Test spinner initialization with custom values"""
    spinner = SpinnerRenderer(
        message="Custom loading", frames=Frames.dash, delay=0.2, clear_message=True
    )
    assert spinner._message == "Custom loading"
    assert spinner._delay == 0.2
    assert spinner._clear_message is True


@pytest.mark.parametrize(
    "decorator,expected_pattern",
    [
        (ColorDecorator(foreground="green"), "\x1b[32mTest message\x1b[0m"),
        (EmojiDecorator("🚀"), "🚀 Test message"),
        (TextWrapDecorator(width=20), "Test message"),
    ],
)
def test_spinner_decorator_application(spinner, decorator, expected_pattern):
    """Test that different decorators are properly applied"""
    spinner.update(decorator)
    spinner.render("Test message")

    assert any(expected_pattern in text for text in spinner._stream.written)


def test_multiple_decorators(spinner):
    """Test applying multiple decorators"""
    spinner.update(ColorDecorator(foreground="blue"))
    spinner.update(EmojiDecorator("⭐"))
    spinner.render("Test message")

    written = spinner._stream.written[-1]
    assert "⭐" in written
    assert "\x1b[34m" in written  # Blue color code
    assert "Test message" in written


def test_spinner_start_stop(spinner):
    """Test starting and stopping the spinner"""
    spinner.start()
    assert isinstance(spinner._spinner_thread, threading.Thread)
    assert spinner._spinner_thread.is_alive()

    spinner.stop()
    assert not spinner._spinner_thread.is_alive()
    assert spinner._done.is_set()


def test_spinner_context_manager(spinner):
    """Test spinner as context manager"""
    with spinner:
        assert spinner._spinner_thread.is_alive()
        time.sleep(0.2)  # Allow some frames to be written

    assert not spinner._spinner_thread.is_alive()
    assert spinner._done.is_set()
    assert len(spinner._stream.written) > 0


def test_spinner_with_colored_text(mock_stream):
    """Test spinner with colored text"""
    spinner = SpinnerRenderer("Loading...", stream=mock_stream)
    spinner.update(ColorDecorator(foreground="cyan"))

    with spinner:
        time.sleep(0.2)

    # Check that color codes are present in output
    assert any("\x1b[36m" in text for text in mock_stream.written)  # Cyan color code
    assert any("\x1b[0m" in text for text in mock_stream.written)  # Reset code


def test_spinner_with_emoji_and_color(mock_stream):
    """Test spinner with both emoji and color decorators"""
    spinner = SpinnerRenderer("Processing...", stream=mock_stream)
    spinner.update(ColorDecorator(foreground="yellow"))
    spinner.update(EmojiDecorator("⚡"))

    with spinner:
        time.sleep(0.2)

    written_text = mock_stream.written
    assert any("⚡" in text for text in written_text)
    assert any("\x1b[33m" in text for text in written_text)  # Yellow color code


def test_spinner_with_text_wrap(mock_stream):
    """Test spinner with text wrapping"""
    long_message = "This is a very long message that should be wrapped"
    spinner = SpinnerRenderer(long_message, stream=mock_stream)
    spinner.update(TextWrapDecorator(width=20))

    with spinner:
        time.sleep(0.2)

    # Verify that the text was wrapped
    written_text = mock_stream.written
    assert any(len(line.strip()) <= 20 for line in written_text)


@pytest.mark.parametrize(
    "frames",
    [
        Frames.default,
        Frames.dash,
        Frames.circular,
        Frames.dots,
        Frames.arrows,
        Frames.moving,
    ],
)
def test_different_frame_styles(mock_stream, frames):
    """Test that all frame styles work correctly"""
    spinner = SpinnerRenderer(
        "Testing frames", stream=mock_stream, frames=frames, delay=0.1
    )

    with spinner:
        time.sleep(0.2)  # Allow some frames to be written

    assert len(mock_stream.written) > 0


def test_spinner_clear_message(mock_stream):
    """Test that clear_message properly clears the spinner message"""
    spinner = SpinnerRenderer("Clear me", stream=mock_stream, clear_message=True)

    with spinner:
        time.sleep(0.2)

    # Verify any written message contains clear spaces
    written_text = mock_stream.written
    assert any(" " * (len("Clear me") + 2) + "\r" in text for text in written_text)
