import logging

from dasbus.constants import DBUS_NAME_FLAG_REPLACE_EXISTING
from dasbus.loop import EventLoop

from command_line_assistant.config import Config
from command_line_assistant.dbus.constants import SERVICE_IDENTIFIER, SESSION_BUS
from command_line_assistant.dbus.definitions import ProcessContext, QueryInterface

logger = logging.getLogger(__name__)


def serve(config: Config):
    """Start the daemon."""
    logger.info("Starting clad!")
    try:
        process_context = ProcessContext(config=config)
        SESSION_BUS.publish_object(
            SERVICE_IDENTIFIER.object_path, QueryInterface(process_context)
        )

        # The flag DBUS_NAME_FLAG_REPLACE_EXISTING is needed during development
        # so ew can replace the existing bus.
        # TODO(r0x0d): See what to do with it later.
        SESSION_BUS.register_service(
            SERVICE_IDENTIFIER.service_name, flags=DBUS_NAME_FLAG_REPLACE_EXISTING
        )
        loop = EventLoop()
        loop.run()
    finally:
        # Unregister the DBus service and objects.
        SESSION_BUS.disconnect()
