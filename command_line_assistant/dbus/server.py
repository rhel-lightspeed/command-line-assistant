"""D-Bus server definition"""

import logging

from dasbus.loop import EventLoop

from command_line_assistant.config import Config
from command_line_assistant.dbus.constants import (
    HISTORY_IDENTIFIER,
    QUERY_IDENTIFIER,
    SYSTEM_BUS,
)
from command_line_assistant.dbus.context import (
    DaemonContext,
)
from command_line_assistant.dbus.interfaces import HistoryInterface, QueryInterface

logger = logging.getLogger(__name__)


def serve(config: Config):
    """Main function to serve and start the daemon server.

    Args:
        config (Config): An instance of the configuration class.
    """
    logger.info("Starting clad!")
    try:
        SYSTEM_BUS.publish_object(
            QUERY_IDENTIFIER.object_path, QueryInterface(DaemonContext(config))
        )
        SYSTEM_BUS.publish_object(
            HISTORY_IDENTIFIER.object_path, HistoryInterface(DaemonContext(config))
        )

        SYSTEM_BUS.register_service(QUERY_IDENTIFIER.service_name)
        SYSTEM_BUS.register_service(HISTORY_IDENTIFIER.service_name)

        loop = EventLoop()
        loop.run()
    finally:
        # Unregister the DBus service and objects.
        SYSTEM_BUS.disconnect()
