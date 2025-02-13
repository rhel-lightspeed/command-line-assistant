import pytest
import responses

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
def test_handle_query(default_payload, mock_config):
    responses.post(
        url="http://localhost/infer",
        json={
            "data": {"text": "test"},
        },
    )

    result = query.submit(default_payload, config=mock_config)
    assert result == "test"


@responses.activate
def test_handle_query_raising_status(mock_config, default_payload):
    responses.post(
        url="http://localhost/infer",
        status=404,
    )
    with pytest.raises(
        RequestFailedError,
        match="There was a problem communicating with the server. Please, try again in a few minutes.",
    ):
        query.submit(default_payload, config=mock_config)


@responses.activate
def test_disable_ssl_verification(caplog, default_payload, mock_config):
    mock_config.backend.auth.verify_ssl = False
    responses.post(url="http://localhost/infer", json={"data": {"text": "yeah, test!"}})

    result = query.submit(default_payload, config=mock_config)
    assert result == "yeah, test!"
    assert (
        "Disabling SSL verification as per user requested."
        in caplog.records[-2].message
    )
