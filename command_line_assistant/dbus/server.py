"""D-Bus server definition"""

import logging

from dasbus.loop import EventLoop
from dasbus.server.handler import ServerObjectHandler
from dasbus.typing import unwrap_variant

from command_line_assistant.config import Config
from command_line_assistant.dbus.constants import (
    CHAT_IDENTIFIER,
    HISTORY_IDENTIFIER,
    SYSTEM_BUS,
    USER_IDENTIFIER,
)
from command_line_assistant.dbus.context import DaemonContext
from command_line_assistant.dbus.interfaces.chat import ChatInterface
from command_line_assistant.dbus.interfaces.history import HistoryInterface
from command_line_assistant.dbus.interfaces.user import UserInterface
from command_line_assistant.dbus.sender_context import sender_context

logger = logging.getLogger(__name__)


class SpecialServerObjectHandler(ServerObjectHandler):
    """Server object handler that inserts sender into the parameters."""

    def _method_callback(self, invocation, interface_name, method_name, parameters):
        """Override the default method callback to insert sender into the parameters."""
        sender = invocation.get_sender()

        try:
            member = self._find_member_spec(interface_name, method_name)
            result = self._handle_call(
                interface_name, method_name, *unwrap_variant(parameters), sender=sender
            )
            self._handle_method_result(invocation, member, result)
        except Exception as error:  # pylint: disable=broad-except
            self._handle_method_error(invocation, interface_name, method_name, error)

    def _handle_call(self, interface_name, method_name, *parameters, sender=None):
        """Override the default call handler to insert sender into the parameters."""
        handler = self._find_handler(interface_name, method_name)

        # Use thread-local context to store sender information
        with sender_context(sender):
            return handler(*parameters)


def _dbus_setup(objects: list[tuple]) -> None:
    """Setup the DBus server and publish the objects.

    Arguments:
        objects (list[tuple]): A tuple of objects to publish.
    """
    for obj, interface in objects:
        SYSTEM_BUS.publish_object(
            obj.object_path, interface, server_factory=SpecialServerObjectHandler
        )
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
