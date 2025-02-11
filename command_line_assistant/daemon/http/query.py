"""Module to handle the query submission to the backend."""

import json
import logging

from requests import RequestException

from command_line_assistant.config import Config
from command_line_assistant.daemon.http.session import get_session
from command_line_assistant.dbus.exceptions import RequestFailedError

logger = logging.getLogger(__name__)


def submit(payload: dict, config: Config) -> str:
    """Method to submit the query to the backend.

    Arguments:
        payload (dict): User query config (Config): Instance of a config class

    Raises:
        RequestFailedError: In case the request can't processed or there is an
        internal error in the backend.

    Returns:
        str: The response from the backend.
    """
    query_endpoint = f"{config.backend.endpoint}/infer"

    try:
        with get_session(config) as session:
            response = session.post(
                query_endpoint, data=json.dumps(payload), timeout=30
            )
        logger.info("Got response from LLM backend")
        response.raise_for_status()
        data = response.json()
        data = data.get("data", {})
        return data.get("text", "")
    except RequestException as e:
        logger.error("Failed to get response from AI: %s", e)
        raise RequestFailedError(
            "There was a problem communicating with the server. Please, try again in a few minutes."
        ) from e
