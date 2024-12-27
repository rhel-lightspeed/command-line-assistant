"""D-Bus server definition"""

import logging

from dasbus.constants import DBUS_NAME_FLAG_REPLACE_EXISTING
from dasbus.loop import EventLoop

from command_line_assistant.config import Config
from command_line_assistant.dbus.constants import (
    HISTORY_IDENTIFIER,
    QUERY_IDENTIFIER,
    SYSTEM_BUS,
)
from command_line_assistant.dbus.context import HistoryContext, QueryContext
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
            QUERY_IDENTIFIER.object_path, QueryInterface(QueryContext(config))
        )
        SYSTEM_BUS.publish_object(
            HISTORY_IDENTIFIER.object_path, HistoryInterface(HistoryContext(config))
        )

        # The flag DBUS_NAME_FLAG_REPLACE_EXISTING is needed during development
        # so ew can replace the existing bus.
        # TODO(r0x0d): See what to do with it later.
        SYSTEM_BUS.register_service(QUERY_IDENTIFIER.service_name)
        SYSTEM_BUS.register_service(
            HISTORY_IDENTIFIER.service_name, flags=DBUS_NAME_FLAG_REPLACE_EXISTING
        )
        loop = EventLoop()
        loop.run()
    finally:
        # Unregister the DBus service and objects.
        SYSTEM_BUS.disconnect()
