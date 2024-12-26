import json
import logging

from requests import RequestException

from command_line_assistant.config import Config
from command_line_assistant.daemon.http.session import get_session
from command_line_assistant.dbus.exceptions import RequestFailedError
from command_line_assistant.handlers import handle_caret

logger = logging.getLogger(__name__)


def submit(query: str, config: Config) -> str:
    """Method to submit the query to the backend.

    Returns:
        The response from the API.
    """
    query = handle_caret(query, config)

    query_endpoint = f"{config.backend.endpoint}/infer"
    payload = {"question": query}

    try:
        logger.info("Waiting for response from AI...")
        logger.debug("User query: %s", query)

        with get_session(config) as session:
            response = session.post(
                query_endpoint, data=json.dumps(payload), timeout=30
            )

        response.raise_for_status()
        data = response.json()
        data = data.get("data", {})
        return data.get("text", "")
    except RequestException as e:
        logger.error("Failed to get response from AI: %s", e)
        raise RequestFailedError(
            "There was a problem communicating with the server. Please, try again in a few minutes."
        ) from e
