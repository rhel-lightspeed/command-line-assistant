import logging
import sys

from command_line_assistant.config import load_config_file
from command_line_assistant.dbus.server import serve
from command_line_assistant.logger import setup_logging

logger = logging.getLogger(__name__)


def daemonize() -> int:
    """Main start point for clad."""
    # Load up the configuration file
    config = load_config_file()
    setup_logging(config)
    serve(config)

    return 0


if __name__ == "__main__":
    sys.exit(daemonize())
