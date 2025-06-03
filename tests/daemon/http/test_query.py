from http import HTTPStatus

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
def test_handle_query_raising_status_from_api(mock_config, default_payload):
    responses.post(
        url="http://localhost/infer", status=404, json={"detail": "Not found"}
    )
    with pytest.raises(
        RequestFailedError,
        match="Resource not found: The requested endpoint doesn't exist. Not found",
    ):
        query.submit(default_payload, config=mock_config)


@responses.activate
def test_handle_query_raising_status_from_gateway(mock_config, default_payload):
    responses.post(
        url="http://localhost/infer",
        status=404,
        json={"errors": [{"status": 404, "detail": "Not found"}]},
    )
    with pytest.raises(
        RequestFailedError,
        match="Resource not found: The requested endpoint doesn't exist. Not found",
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


@responses.activate
def test_submit_empty_query(mock_config):
    """Test submitting an empty query"""
    empty_payload = {
        "question": "",
        "context": {
            "stdin": "",
            "attachment": {"contents": "", "mimetype": "unknown/unknown"},
        },
    }

    responses.post(
        url="http://localhost/infer",
        json={"data": {"text": ""}},
    )

    result = query.submit(empty_payload, config=mock_config)
    assert result == ""


error_case_names = "status_code,detail,expected_error_message"
error_case_values = [
    # 4xx Client Errors
    (
        HTTPStatus.BAD_REQUEST,
        "Invalid request format",
        "Bad request: The server couldn't understand the request. Invalid request format",
    ),
    (
        HTTPStatus.UNAUTHORIZED,
        "Invalid API key",
        "Authentication failed: Please check your credentials. Invalid API key",
    ),
    (
        HTTPStatus.PAYMENT_REQUIRED,
        "Monthly token quota exceeded",
        "Quota exceeded: You've reached your usage limit. Please upgrade your plan or try again later. Monthly token quota exceeded",
    ),
    (
        HTTPStatus.FORBIDDEN,
        "Access denied",
        "Access forbidden: You don't have permission to access this resource. Access denied",
    ),
    (
        HTTPStatus.NOT_FOUND,
        "Endpoint not found",
        "Resource not found: The requested endpoint doesn't exist. Endpoint not found",
    ),
    (
        HTTPStatus.METHOD_NOT_ALLOWED,
        "Method not allowed",
        "Method not allowed: The request method is not supported for the requested resource. Method not allowed",
    ),
    (
        HTTPStatus.PROXY_AUTHENTICATION_REQUIRED,
        "Proxy authentication required",
        "Proxy authentication required: The request requires authentication with the proxy. Proxy authentication required",
    ),
    (
        HTTPStatus.REQUEST_TIMEOUT,
        "Request timed out",
        "Request timeout: The server timed out waiting for the request. Request timed out",
    ),
    (
        HTTPStatus.CONFLICT,
        "Resource conflict",
        "Conflict: The request conflicts with the current state of the server. Resource conflict",
    ),
    (
        HTTPStatus.TOO_MANY_REQUESTS,
        "Rate limit reached. Try again in 60 seconds.",
        "Too many requests: Rate limit exceeded. Please try again later. Rate limit reached. Try again in 60 seconds.",
    ),
    # 5xx Server Errors
    (
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "Backend service is experiencing issues",
        "Server error: The backend service encountered an internal error. Please try again later. Backend service is experiencing issues",
    ),
    (
        HTTPStatus.NOT_IMPLEMENTED,
        "Feature not implemented",
        "Not implemented: The server does not support the functionality required to fulfill the request. Feature not implemented",
    ),
]


@responses.activate
@pytest.mark.parametrize(error_case_names, error_case_values)
def test_handle_error_responses_from_api(
    mock_config, default_payload, status_code, detail, expected_error_message
):
    """Test handling various HTTP error codes from 4xx to 5xx received from the
    API."""
    responses.post(
        url="http://localhost/infer",
        status=status_code,
        json={"detail": detail},
    )

    with pytest.raises(RequestFailedError, match=expected_error_message):
        query.submit(default_payload, config=mock_config)


@responses.activate
@pytest.mark.parametrize(error_case_names, error_case_values)
def test_handle_error_responses_from_gateway(
    mock_config, default_payload, status_code, detail, expected_error_message
):
    """Test handling various HTTP error codes from 4xx to 5xx received from
    3scale."""
    responses.post(
        url="http://localhost/infer",
        status=status_code,
        json={"errors": [{"status": status_code, "detail": detail}]},
    )

    with pytest.raises(RequestFailedError, match=expected_error_message):
        query.submit(default_payload, config=mock_config)


@responses.activate
def test_extract_response_text_invalid_json(mock_config, default_payload):
    """Test handling non-JSON responses"""
    responses.post(
        url="http://localhost/infer",
        body="Not a JSON response",
        content_type="text/plain",
    )

    result = query.submit(default_payload, config=mock_config)
    assert result == "Not a JSON response"


@responses.activate
@pytest.mark.parametrize(
    "status_code,response_body,expected_error_message",
    [
        (
            HTTPStatus.NOT_FOUND,
            "Not found",
            "Resource not found: The requested endpoint doesn't exist. No additional details provided.",
        )
    ],
)
def test_handle_error_response_invalid_json(
    mock_config, default_payload, status_code, response_body, expected_error_message
):
    """Test handling non-JSON error responses"""
    responses.post(
        url="http://localhost/infer",
        status=status_code,
        body=response_body,
        content_type="text/plain",
    )

    with pytest.raises(RequestFailedError, match=expected_error_message):
        query.submit(default_payload, config=mock_config)
