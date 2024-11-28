import pytest
import requests
import responses

from command_line_assistant.config import Config
from command_line_assistant.config.schemas import AuthSchema, BackendSchema
from command_line_assistant.daemon.http import query


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

    result = query.submit(query="test", config=config)

    assert result == "yeah, test!\n\nReferences:\nyes: http://localhost/super/secret"


@responses.activate
def test_handle_query_raising_status():
    responses.post(
        url="http://localhost",
        status=404,
    )
    config = Config(backend=BackendSchema(endpoint="http://localhost"))
    with pytest.raises(requests.exceptions.RequestException):
        query.submit(query="test", config=config)


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
        backend=BackendSchema(
            endpoint="https://localhost", auth=AuthSchema(verify_ssl=False)
        )
    )

    result = query.submit(query="test", config=config)

    assert result == "yeah, test!\n\nReferences:\nyes: http://localhost/super/secret"
    assert "Disabling SSL verification." in caplog.records[2].message
