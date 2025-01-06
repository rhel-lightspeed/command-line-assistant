import threading
from unittest.mock import patch

import pytest

from command_line_assistant.utils import renderers


def test_create_error_renderer(capsys: pytest.CaptureFixture[str]):
    renderer = renderers.create_error_renderer()
    renderer.render("errored out")

    captured = capsys.readouterr()
    print(captured)
    assert "\x1b[31m🙁 errored out\x1b[0m\n" in captured.out


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
    print(captured)
    assert "rrored out\n" in captured.out
