import os
from unittest import mock

import pytest
import requests
import responses

from command_line_assistant import handlers
from command_line_assistant.config import Config
from command_line_assistant.config.schemas import BackendSchema, OutputSchema


@responses.activate
def test_handle_query():
    responses.post(
        url="http://localhost",
        json={
            "response": "yeah, test!",
            "referenced_documents": [
                {"title": "yes", "docs_url": "http://localhost/super/secret"}
            ],
        },
    )

    config = Config(backend=BackendSchema(endpoint="http://localhost"))

    result = handlers.handle_query(query="test", config=config)

    assert result == "yeah, test!\n\nReferences:\nyes: http://localhost/super/secret"


@responses.activate
def test_handle_query_raising_status():
    responses.post(
        url="http://localhost",
        status=404,
    )
    config = Config(backend=BackendSchema(endpoint="http://localhost"))
    with pytest.raises(requests.exceptions.RequestException):
        handlers.handle_query(query="test", config=config)


@responses.activate
def test_disable_ssl_verification(caplog):
    responses.post(
        url="https://localhost",
        json={
            "response": "yeah, test!",
            "referenced_documents": [
                {"title": "yes", "docs_url": "http://localhost/super/secret"}
            ],
        },
    )

    config = Config(
        backend=BackendSchema(endpoint="https://localhost", verify_ssl=False)
    )

    result = handlers.handle_query(query="test", config=config)

    assert result == "yeah, test!\n\nReferences:\nyes: http://localhost/super/secret"
    assert "Disabling SSL verification." in caplog.records[-1].message


def test_handle_caret_early_skip():
    result = handlers._handle_caret(query="early skip", config=Config())
    assert "early skip" == result


def test_handle_caret_file_missing(tmp_path):
    non_existing_file = tmp_path / "something.tmp"
    with pytest.raises(ValueError):
        handlers._handle_caret(
            query="^test", config=Config(output=OutputSchema(file=non_existing_file))
        )


def test_handle_caret(tmp_path):
    output_file = tmp_path / "output_file.tmp"
    output_file.write_text("cmd from file")
    result = handlers._handle_caret(
        query="^test", config=Config(output=OutputSchema(file=output_file))
    )

    assert "Context data: cmd from file\nQuestion: test" == result


def test_handle_script_session(tmp_path, monkeypatch):
    output_file = tmp_path / "output.tmp"
    output_file.write_text("hi!")
    monkeypatch.setattr(os, "system", mock.Mock())

    handlers.handle_script_session(output_file)

    assert not output_file.exists()
