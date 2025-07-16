"""Module to handle the query submission to the backend."""

import logging
from http import HTTPStatus
from json.decoder import JSONDecodeError

from requests import RequestException, Response

from command_line_assistant.config import Config
from command_line_assistant.daemon.http.session import get_session
from command_line_assistant.dbus.exceptions import RequestFailedError

logger = logging.getLogger(__name__)

#: Map status codes to error messages
ERROR_MESSAGES: dict[int, str] = {
    # 4xx status codes
    HTTPStatus.BAD_REQUEST: "Bad request: The server couldn't understand the request. {detailed_message}",
    HTTPStatus.UNAUTHORIZED: "Authentication failed: Please check your credentials. {detailed_message}",
    HTTPStatus.PAYMENT_REQUIRED: "Quota exceeded: You've reached your usage limit. Please upgrade your plan or try again later. {detailed_message}",
    HTTPStatus.FORBIDDEN: "Access forbidden: You don't have permission to access this resource. {detailed_message}",
    HTTPStatus.NOT_FOUND: "Resource not found: The requested endpoint doesn't exist. {detailed_message}",
    HTTPStatus.METHOD_NOT_ALLOWED: "Method not allowed: The request method is not supported for the requested resource. {detailed_message}",
    HTTPStatus.PROXY_AUTHENTICATION_REQUIRED: "Proxy authentication required: The request requires authentication with the proxy. {detailed_message}",
    HTTPStatus.CONFLICT: "Conflict: The request conflicts with the current state of the server. {detailed_message}",
    HTTPStatus.GONE: "Gone: The requested resource is no longer available. {detailed_message}",
    HTTPStatus.PRECONDITION_FAILED: "Precondition failed: The server does not meet one of the preconditions in the request. {detailed_message}",
    HTTPStatus.REQUEST_ENTITY_TOO_LARGE: "Request entity too large: The request is larger than the server is willing to process. {detailed_message}",
    HTTPStatus.REQUEST_URI_TOO_LONG: "Request URI too long: The URI provided was too long for the server to process. {detailed_message}",
    HTTPStatus.UNSUPPORTED_MEDIA_TYPE: "Unsupported media type: The request content type is not supported. {detailed_message}",
    HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE: "Requested range not satisfiable: The requested range is not available. {detailed_message}",
    HTTPStatus.EXPECTATION_FAILED: "Expectation failed: The server cannot meet the requirements of the Expect request-header field. {detailed_message}",
    HTTPStatus.UNPROCESSABLE_ENTITY: "Unprocessable entity: The request was well-formed but semantically incorrect. {detailed_message}",
    HTTPStatus.LOCKED: "Locked: The resource is locked. {detailed_message}",
    HTTPStatus.FAILED_DEPENDENCY: "Failed dependency: The request failed due to failure of a previous request. {detailed_message}",
    HTTPStatus.UPGRADE_REQUIRED: "Upgrade required: The client should switch to a different protocol. {detailed_message}",
    HTTPStatus.PRECONDITION_REQUIRED: "Precondition required: The server requires the request to be conditional. {detailed_message}",
    HTTPStatus.TOO_MANY_REQUESTS: "Too many requests: Rate limit exceeded. Please try again later. {detailed_message}",
    HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE: "Request header fields too large: The header fields exceed the maximum size. {detailed_message}",
    HTTPStatus.UNAVAILABLE_FOR_LEGAL_REASONS: "Unavailable for legal reasons: The requested resource is unavailable due to legal reasons. {detailed_message}",
    HTTPStatus.REQUEST_TIMEOUT: "Request timeout: The server timed out waiting for the request. {detailed_message}",
    # 5xx status codes
    HTTPStatus.INTERNAL_SERVER_ERROR: "Server error: The backend service encountered an internal error. Please try again later. {detailed_message}",
    HTTPStatus.NOT_IMPLEMENTED: "Not implemented: The server does not support the functionality required to fulfill the request. {detailed_message}",
    HTTPStatus.BAD_GATEWAY: "Bad gateway: The backend server received an invalid response. Please try again later. {detailed_message}",
    HTTPStatus.SERVICE_UNAVAILABLE: "Service unavailable: The backend service is temporarily unavailable. Please try again later. {detailed_message}",
    HTTPStatus.GATEWAY_TIMEOUT: "Gateway timeout: The backend service took too long to respond. Please try again later. {detailed_message}",
    HTTPStatus.HTTP_VERSION_NOT_SUPPORTED: "HTTP version not supported: The server does not support the HTTP protocol version used in the request. {detailed_message}",
    HTTPStatus.VARIANT_ALSO_NEGOTIATES: "Variant also negotiates: The server has an internal configuration error. {detailed_message}",
    HTTPStatus.INSUFFICIENT_STORAGE: "Insufficient storage: The server has insufficient storage to complete the request. {detailed_message}",
    HTTPStatus.LOOP_DETECTED: "Loop detected: The server detected an infinite loop while processing the request. {detailed_message}",
    HTTPStatus.NOT_EXTENDED: "Not extended: Further extensions to the request are required for the server to fulfill it. {detailed_message}",
    HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED: "Network authentication required: The client needs to authenticate to gain network access. {detailed_message}",
}


def submit(payload: dict, config: Config) -> str:
    """Submit a query to the backend API.

    Args:
        payload: JSON-serializable dictionary containing the query parameters
        config: Configuration object with backend endpoint information

    Raises:
        RequestFailedError: If the request fails due to network issues,
                           authentication problems, or server errors

    Returns:
        str: The response text from the backend
    """
    query_endpoint = f"{config.backend.endpoint}/infer"

    try:
        response = _send_request(query_endpoint, payload, config)
        logger.info("Received response from LLM backend")

        if response.status_code != HTTPStatus.OK:
            _handle_error_response(response)

        return _extract_response_text(response)
    except RequestException as exc:
        logger.error("Failed to get response from AI: %s", exc)
        raise RequestFailedError(
            f"Communication error with the server: {str(exc)}. Please try again in a few minutes."
        ) from exc
    except OSError as exc:
        # If the exception string contains the standard RHSM cert path, assume
        # the system is not registered and raise a very specific error message.
        if "/etc/pki/consumer/cert.pem" in str(exc):
            raise RequestFailedError(
                "The system must be registered to use RHEL Lightspeed. For cloud-based systems, see: https://access.redhat.com/articles/7127962"
            ) from exc
        raise exc


def _send_request(endpoint: str, payload: dict, config: Config) -> Response:
    """Send POST request to the backend.

    Args:
        endpoint: Full URL endpoint
        payload: Request payload
        config: Configuration with auth settings

    Returns:
        Response object
    """
    with get_session(config) as session:
        return session.post(
            endpoint,
            json=payload,  # Uses json parameter instead of manually serializing
            timeout=config.backend.timeout,
        )


def _handle_error_response(response: Response) -> None:
    """Check response for errors and raise appropriate exceptions.

    Args:
        response: Response object to check

    Raises:
        RequestFailedError: If response status code indicates an error
    """
    # Get the error message from the predefined map, or create a generic one
    error_message = ERROR_MESSAGES.get(
        response.status_code,
        f"Unexpected error with status code {response.status_code}: {response.reason}",
    )
    detailed_message = "No additional details provided."
    try:
        response_json = response.json()
        if "errors" in response_json and isinstance(response_json["errors"], list):
            # 3scale returns errors wrapped in a JSON object with a list of errors
            for error in response.json()["errors"]:
                if error["status"] == response.status_code and "detail" in error:
                    detailed_message = error["detail"]
                    break
        elif "detail" in response_json:
            # Assume the response is directly from the API that contains just a
            # single "detail" field.
            detailed_message = response_json["detail"]
    except JSONDecodeError as e:
        # Catch the JSONDecodeError and log it to the debug log, but continue
        # the error creation.
        logger.debug("Failed to decode JSON: %s", e)

    error_message = error_message.format(detailed_message=detailed_message)

    logger.error("Status code: %s and message: %s", response.status_code, error_message)
    raise RequestFailedError(error_message)


def _extract_response_text(response: Response) -> str:
    """Extract text from successful response.

    Args:
        response: Response object with JSON data

    Returns:
        Extracted text from response
    """
    try:
        data = response.json()
        return data.get("data", {}).get("text", "")
    except ValueError:
        logger.warning("Response didn't contain valid JSON")
        return response.text or ""
