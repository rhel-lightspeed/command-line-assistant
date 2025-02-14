"""D-Bus server definition"""

import logging

from dasbus.loop import EventLoop

from command_line_assistant.config import Config
from command_line_assistant.dbus.constants import (
    CHAT_IDENTIFIER,
    HISTORY_IDENTIFIER,
    SYSTEM_BUS,
    USER_IDENTIFIER,
)
from command_line_assistant.dbus.context import (
    DaemonContext,
)
from command_line_assistant.dbus.interfaces.chat import ChatInterface
from command_line_assistant.dbus.interfaces.history import HistoryInterface
from command_line_assistant.dbus.interfaces.user import UserInterface

logger = logging.getLogger(__name__)


def _dbus_setup(objects: list[tuple]) -> None:
    """Setup the DBus server and publish the objects.

    Arguments:
        objects (list[tuple]): A tuple of objects to publish.
    """
    for obj, interface in objects:
        SYSTEM_BUS.publish_object(obj.object_path, interface)
        SYSTEM_BUS.register_service(obj.service_name)


def serve(config: Config):
    """Main function to serve and start the daemon server.

    Arguments:
        config (Config): An instance of the configuration class.
    """
    try:
        logger.info("Setting up service and object names for dbus.")
        _dbus_setup(
            [
                (CHAT_IDENTIFIER, ChatInterface(DaemonContext(config))),
                (HISTORY_IDENTIFIER, HistoryInterface(DaemonContext(config))),
                (USER_IDENTIFIER, UserInterface(DaemonContext(config))),
            ]
        )

        logger.info("Starting clad!")
        loop = EventLoop()
        loop.run()
    finally:
        # Unregister the DBus service and objects.
        SYSTEM_BUS.disconnect()
