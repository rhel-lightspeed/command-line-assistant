"""D-Bus interfaces that defines and powers our commands."""

import logging

from dasbus.server.interface import dbus_interface
from dasbus.server.template import InterfaceTemplate
from dasbus.typing import Int, Str

from command_line_assistant.daemon.session import UserSessionManager
from command_line_assistant.dbus.constants import USER_IDENTIFIER
from command_line_assistant.dbus.context import DaemonContext
from command_line_assistant.dbus.interfaces.authorization import DBusAuthorizationMixin
from command_line_assistant.dbus.sender_context import get_current_sender

logger = logging.getLogger(__name__)


@dbus_interface(USER_IDENTIFIER.interface_name)
class UserInterface(InterfaceTemplate, DBusAuthorizationMixin):
    """The DBus interface of a query."""

    def __init__(self, implementation: DaemonContext):
        """Constructor of the class

        Arguments:
            implementation (DaemonContext): The implementation context to be used in an interface.
        """
        super().__init__(implementation)

        self._session_manager = UserSessionManager()

    def _verify_caller_authorization(self, sender: str, requested_user_id: int) -> None:
        """Verify that the caller is authorized to access the requested user's data.

        Arguments:
            sender: The D-Bus sender.
            requested_user_id (int): The Unix user ID being requested in the method call.

        Raises:
            PermissionError: If the caller's Unix user ID doesn't match the requested user ID.
        """
        self._verify_unix_user_authorization(sender, requested_user_id)

    def GetUserId(self, effective_user_id: Int) -> Str:
        """Get the user ID for the given effective user ID.

        Arguments:
            effective_user_id (Int): The effective user id coming from user space

        Returns:
            Str: The identifier of the user session.
        """
        # Verify caller authorization - ensure caller can only get their own
        # user ID
        sender = get_current_sender()
        self._verify_caller_authorization(sender, effective_user_id)

        return self._session_manager.get_user_id(effective_user_id)
