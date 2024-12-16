import json
import logging

from requests import RequestException

from command_line_assistant.config import Config
from command_line_assistant.daemon.http.session import get_session
from command_line_assistant.handlers import handle_caret

logger = logging.getLogger(__name__)


def submit(query: str, config: Config) -> str:
    """Method to submit the query to the backend.

    Returns:
        The response from the API.
    """
    query = handle_caret(query, config)
    # NOTE: Add more query handling here

    query_endpoint = f"{config.backend.endpoint}/v1/query"
    payload = {"query": query}

    try:
        logger.info("Waiting for response from AI...")
        logger.debug("User query: %s", query)

        with get_session(config) as session:
            response = session.post(
                query_endpoint, data=json.dumps(payload), timeout=30
            )

        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except RequestException as e:
        logger.error("Failed to get response from AI: %s", e)
        raise
