import threading
from unittest.mock import patch

import pytest

from command_line_assistant.rendering import renderers


def test_create_error_renderer(capsys: pytest.CaptureFixture[str]):
    renderer = renderers.create_error_renderer()
    renderer.render("errored out")

    captured = capsys.readouterr()
    assert "\x1b[31m🙁 errored out\x1b[0m\n" in captured.err


def test_create_spinner_renderer(capsys, mock_stream):
    with patch("command_line_assistant.rendering.stream.StdoutStream", mock_stream):
        spinner = renderers.create_spinner_renderer(message="Loading...", decorators=[])
        spinner.start()
        assert isinstance(spinner._spinner_thread, threading.Thread)
        assert spinner._spinner_thread.is_alive()

        spinner.stop()
        assert not spinner._spinner_thread.is_alive()
        assert spinner._done.is_set()

        captured = capsys.readouterr().out
        assert "Loading..." in captured


def test_create_text_renderer(capsys: pytest.CaptureFixture[str]):
    renderer = renderers.create_text_renderer()
    renderer.render("errored out")

    captured = capsys.readouterr()
    assert "rrored out\n" in captured.out


@pytest.mark.parametrize(
    ("size", "expected"),
    (
        # Test bytes (< 1000)
        (0, "0.00 B"),
        (1, "1.00 B"),
        (42, "42.00 B"),
        (248, "248.00 B"),
        (567, "567.00 B"),
        (999, "999.00 B"),
        # Test KB boundary and values
        (1000, "1.00 KB"),
        (999999, "1000.00 KB"),
        # Test MB boundary and values
        (1000000, "1.00 MB"),
        (999999999, "1000.00 MB"),
        # Test GB boundary and values
        (1000000000, "1.00 GB"),
        (999999999999, "1000.00 GB"),
        # Test TB boundary and values
        (1000000000000, "1.00 TB"),
        # Test PB boundary and values
        (1000000000000000, "1.00 PB"),
        # Test float inputs
        (1500.5, "1.50 KB"),
        (2500.75, "2.50 KB"),
        (32000, "32.00 KB"),
        (1234567.89, "1.23 MB"),
        (9876543210.123, "9.88 GB"),
        # Test edge cases and random values
        (1234567, "1.23 MB"),
        (9876543, "9.88 MB"),
        (123456789, "123.46 MB"),
        (987654321, "987.65 MB"),
        (1234567890, "1.23 GB"),
        (9876543210, "9.88 GB"),
    ),
)
def test_human_readable_size(size, expected):
    assert renderers.human_readable_size(size) == expected
