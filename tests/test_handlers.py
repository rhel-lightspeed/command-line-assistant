import os
from unittest import mock

import pytest

from command_line_assistant import handlers
from command_line_assistant.config import Config
from command_line_assistant.config.schemas import OutputSchema


def test_handle_caret_early_skip():
    result = handlers.handle_caret(query="early skip", config=Config())
    assert "early skip" == result


def test_handle_caret_file_missing(tmp_path):
    non_existing_file = tmp_path / "something.tmp"
    with pytest.raises(ValueError):
        handlers.handle_caret(
            query="^test", config=Config(output=OutputSchema(file=non_existing_file))
        )


def test_handle_caret(tmp_path):
    output_file = tmp_path / "output_file.tmp"
    output_file.write_text("cmd from file")
    result = handlers.handle_caret(
        query="^test", config=Config(output=OutputSchema(file=output_file))
    )

    assert "Context data: cmd from file\nQuestion: test" == result


def test_handle_script_session(tmp_path, monkeypatch):
    output_file = tmp_path / "output.tmp"
    output_file.write_text("hi!")
    monkeypatch.setattr(os, "system", mock.Mock())

    handlers.handle_script_session(output_file)

    assert not output_file.exists()
