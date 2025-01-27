import pytest
import responses

from command_line_assistant.config import Config
from command_line_assistant.config.schemas.backend import AuthSchema, BackendSchema
from command_line_assistant.daemon.http import query
from command_line_assistant.dbus.exceptions import RequestFailedError


@pytest.fixture
def default_payload():
    return {
        "question": "test",
        "context": {
            "stdin": "",
            "attachment": {"contents": "", "mimetype": "unknown/unknown"},
        },
    }


@responses.activate
def test_handle_query(default_payload):
    responses.post(
        url="http://localhost/infer",
        json={
            "data": {"text": "test"},
        },
    )

    config = Config(
        backend=BackendSchema(
            endpoint="http://localhost", auth=AuthSchema(verify_ssl=False)
        )
    )

    result = query.submit(default_payload, config=config)

    assert result == "test"


@responses.activate
def test_handle_query_raising_status(default_payload):
    responses.post(
        url="http://localhost/infer",
        status=404,
    )
    config = Config(
        backend=BackendSchema(
            endpoint="http://localhost/infer", auth=AuthSchema(verify_ssl=False)
        )
    )
    with pytest.raises(
        RequestFailedError,
        match="There was a problem communicating with the server. Please, try again in a few minutes.",
    ):
        query.submit(default_payload, config=config)


@responses.activate
def test_disable_ssl_verification(caplog, default_payload):
    responses.post(
        url="https://localhost/infer", json={"data": {"text": "yeah, test!"}}
    )

    config = Config(
        backend=BackendSchema(
            endpoint="https://localhost", auth=AuthSchema(verify_ssl=False)
        )
    )

    result = query.submit(default_payload, config=config)

    assert result == "yeah, test!"
    assert (
        "Disabling SSL verification as per user requested."
        in caplog.records[-1].message
    )
