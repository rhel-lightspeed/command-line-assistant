"""Handle the http sessions that the daemon issues to the backend."""

import logging

import urllib3
from requests.sessions import Session

from command_line_assistant.config import Config
from command_line_assistant.constants import VERSION
from command_line_assistant.daemon.http.adapters import RetryAdapter

#: Define the custom user agent for clad
USER_AGENT = f"clad/{VERSION}"

logger = logging.getLogger(__name__)


def get_session(config: Config) -> Session:
    """Retrieve a Session object with SSL capabilities.

    We need to be extra careful here. If there is any cookies that identify the
    user/conversation, we will need to think about how to handle that in a
    multi-user scenario. Currently, we don't have that implemented.

    For now, we only mount the TLS information to the endpoint.

    Arguments:
        config (Config): Instance of the config class

    Returns:
        Session: A mounted session with the necessary adapters.
    """
    session = Session()

    # Include the proxies defined by the user. By default, nothing is loaded.
    session.proxies.update(config.backend.proxies)

    # Set up the necessary headers for every session.
    session.headers["User-Agent"] = USER_AGENT
    session.headers["Content-Type"] = "application/json"

    retry_adapter = RetryAdapter()

    session.mount(config.backend.endpoint, retry_adapter)

    if not config.backend.auth.verify_ssl:  # type: ignore
        logger.warning("Disabling SSL verification as per user requested.")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session.verify = False
        return session

    session.cert = (config.backend.auth.cert_file, config.backend.auth.key_file)  # type: ignore

    return session
