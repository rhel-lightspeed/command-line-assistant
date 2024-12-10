import sys
import threading
import time
from contextlib import contextmanager
from io import StringIO

import pytest

from command_line_assistant.rendering.spinner import Frames, ascii_spinner


@contextmanager
def capture_stdout():
    """Helper context manager to capture stdout for testing"""
    stdout = StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout
    try:
        yield stdout
    finally:
        sys.stdout = old_stdout


def test_frames_default_values():
    """Test that Frames class has all expected default values"""
    frames = Frames()

    # Test that all frame sequences exist
    assert hasattr(frames, "default")
    assert hasattr(frames, "braille")
    assert hasattr(frames, "circular")
    assert hasattr(frames, "dots")
    assert hasattr(frames, "arrows")
    assert hasattr(frames, "moving")


def test_frames_iteration():
    """Test that frame sequences can be iterated"""
    frames = Frames()

    # Test default frames iteration
    default_iterator = frames.default
    first_frame = next(default_iterator)
    assert first_frame in ["-", "\\", "|", "/"]

    # Test that it cycles
    for _ in range(5):  # More than number of frames
        frame = next(default_iterator)
        assert frame in ["-", "\\", "|", "/"]


def test_ascii_spinner_basic():
    """Test basic spinner functionality"""
    with capture_stdout() as output:
        with ascii_spinner("Loading", delay=0.1):
            time.sleep(0.2)  # Allow spinner to make at least one iteration

        captured = output.getvalue()
        assert "Loading" in captured
        assert "\r" in captured  # Should use carriage return


def test_ascii_spinner_clear_message():
    """Test spinner with clear_message option"""
    with capture_stdout() as output:
        with ascii_spinner("Loading", clear_message=True, delay=0.1):
            time.sleep(0.2)

        final_output = output.getvalue().split("\r")[-1]
        assert len(final_output.strip()) == 0  # Should end with empty line


def test_ascii_spinner_custom_frames():
    """Test spinner with custom frames"""
    custom_frames = iter(["A", "B", "C"])
    with capture_stdout() as output:
        with ascii_spinner("Loading", frames=custom_frames, delay=0.1):
            time.sleep(0.2)

        captured = output.getvalue()
        assert any(frame in captured for frame in ["A", "B", "C"])


def test_spinner_thread_cleanup():
    """Test that spinner properly cleans up its thread"""
    initial_threads = threading.active_count()

    with ascii_spinner("Loading", delay=0.1):
        time.sleep(0.2)
        during_threads = threading.active_count()
        assert during_threads > initial_threads  # Should have one more thread

    time.sleep(0.2)  # Give time for cleanup
    after_threads = threading.active_count()
    assert after_threads == initial_threads  # Thread should be cleaned up


@pytest.mark.parametrize("delay", [0.1, 0.2, 0.5])
def test_spinner_different_delays(delay):
    """Test spinner with different delay values"""
    start_time = time.time()
    with ascii_spinner("Loading", delay=delay):
        time.sleep(delay * 2)  # Wait for at least 2 iterations
    duration = time.time() - start_time

    assert duration >= delay * 2
