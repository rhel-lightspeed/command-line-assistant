import pytest
import requests
import responses

from command_line_assistant.config import Config
from command_line_assistant.config.schemas import AuthSchema, BackendSchema
from command_line_assistant.daemon.http import query


@responses.activate
def test_handle_query():
    responses.post(
        url="http://localhost/infer",
        json={
            "answer": "test",
        },
    )

    config = Config(
        backend=BackendSchema(
            endpoint="http://localhost", auth=AuthSchema(verify_ssl=False)
        )
    )

    result = query.submit(query="test", config=config)

    assert result == "test"


@responses.activate
def test_handle_query_raising_status():
    responses.post(
        url="http://localhost/infer",
        status=404,
    )
    config = Config(
        backend=BackendSchema(
            endpoint="http://localhost/infer", auth=AuthSchema(verify_ssl=False)
        )
    )
    with pytest.raises(requests.exceptions.RequestException):
        query.submit(query="test", config=config)


@responses.activate
def test_disable_ssl_verification(caplog):
    responses.post(url="https://localhost/infer", json={"answer": "yeah, test!"})

    config = Config(
        backend=BackendSchema(
            endpoint="https://localhost", auth=AuthSchema(verify_ssl=False)
        )
    )

    result = query.submit(query="test", config=config)

    assert result == "yeah, test!"
    assert (
        "Disabling SSL verification as per user requested." in caplog.records[2].message
    )
