"""D-Bus interfaces that defines and powers our commands."""

import logging

from dasbus.server.interface import dbus_interface
from dasbus.server.template import InterfaceTemplate
from dasbus.typing import Int, Str

from command_line_assistant.daemon.session import UserSessionManager
from command_line_assistant.dbus.constants import USER_IDENTIFIER
from command_line_assistant.dbus.context import DaemonContext

logger = logging.getLogger(__name__)


@dbus_interface(USER_IDENTIFIER.interface_name)
class UserInterface(InterfaceTemplate):
    """The DBus interface of a query."""

    def __init__(self, implementation: DaemonContext):
        """Constructor of the class

        Arguments:
            implementation (DaemonContext): The implementation context to be used in an interface.
        """
        super().__init__(implementation)

        self._session_manager = UserSessionManager()

    def GetUserId(self, effective_user_id: Int) -> Str:
        """Get the user ID for the given effective user ID.

        Arguments:
            effective_user_id (Int): The effective user id coming from user space

        Returns:
            Str: The identifier of the user session.
        """
        return self._session_manager.get_user_id(effective_user_id)
