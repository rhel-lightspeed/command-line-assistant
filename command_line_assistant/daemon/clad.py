"""Module that is the entrypoint for the daemon that will run in systemd."""

import logging
import sys

from command_line_assistant.config import load_config_file
from command_line_assistant.dbus.server import serve
from command_line_assistant.logger import setup_daemon_logging

logger = logging.getLogger(__name__)


def daemonize() -> int:
    """Main start point for the clad binary.

    Returns:
        int: The status code.
    """
    # Load up the configuration file
    config = load_config_file()
    setup_daemon_logging(config)
    serve(config)

    return 0


if __name__ == "__main__":
    sys.exit(daemonize())
