"""D-Bus authorization mixin for interface classes."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from command_line_assistant.daemon.session import UserSessionManager

logger = logging.getLogger(__name__)


class DBusAuthorizationMixin:
    """Mixin class providing D-Bus caller authorization functionality."""

    def _get_caller_unix_user_id(self, sender: str) -> int:
        """Get the Unix user ID of the D-Bus caller.

        Arguments:
            sender: The D-Bus sender.

        Returns:
            int: The Unix user ID of the caller.

        Raises:
            PermissionError: If caller information cannot be retrieved.
        """
        try:
            # Access the D-Bus connection through the system bus
            from command_line_assistant.dbus.constants import SYSTEM_BUS

            dbus_proxy = SYSTEM_BUS.get_proxy(
                "org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus",
            )
            # Get the UNIX user ID of the caller
            sender_unix_id = dbus_proxy.GetConnectionUnixUser(sender)  # type: ignore
            logger.debug(
                "Retrieved Unix user ID %d for sender '%s'", sender_unix_id, sender
            )
            return sender_unix_id

        except Exception as e:
            logger.warning("Could not get caller Unix user ID: %s", e)
            raise PermissionError("Failed to retrieve caller information") from e

    def _verify_unix_user_authorization(
        self, sender: str, requested_unix_user_id: int
    ) -> None:
        """Verify that the caller's Unix user ID matches the requested Unix user ID.

        Arguments:
            sender: The D-Bus sender.
            requested_unix_user_id (int): The Unix user ID being requested.

        Raises:
            PermissionError: If the caller's Unix user ID doesn't match the requested user ID.
        """
        try:
            caller_unix_id = self._get_caller_unix_user_id(sender)

            # Reject the request if the Unix user ID of the caller is different
            # from the Unix user ID being requested
            if requested_unix_user_id != caller_unix_id:
                logger.warning(
                    "Authorization failed: caller Unix user ID '%d' does not match requested Unix user ID '%d'",
                    caller_unix_id,
                    requested_unix_user_id,
                    extra={"audit": True},
                )
                raise PermissionError("Unix user ID mismatch: access denied")

            logger.debug(
                "Unix user authorization successful for user ID '%d'",
                requested_unix_user_id,
            )

        except PermissionError:
            # Re-raise permission errors
            raise
        except Exception as e:
            logger.warning("Could not verify Unix user authorization: %s", e)
            # For security, fail closed - if we can't verify, deny access
            raise PermissionError("Authorization verification failed") from e

    def _verify_internal_user_authorization(
        self, sender: str, requested_user_id: str, session_manager: "UserSessionManager"
    ) -> None:
        """Verify that the caller is authorized to access the requested internal user's data.

        Arguments:
            sender: The D-Bus sender.
            requested_user_id (str): The internal user ID being requested.
            session_manager: UserSessionManager instance for user ID conversion.

        Raises:
            PermissionError: If the caller's user ID doesn't match the requested user ID.
        """
        try:
            caller_unix_id = self._get_caller_unix_user_id(sender)
            # Convert UNIX user ID to our internal user ID format
            caller_internal_id = session_manager.get_user_id(caller_unix_id)

            # Reject the request if the internal user ID of the caller is different
            # from the internal user ID being requested
            if requested_user_id != caller_internal_id:
                logger.warning(
                    "Authorization failed: caller user ID '%s' does not match requested user ID '%s'",
                    caller_internal_id,
                    requested_user_id,
                    extra={"audit": True},
                )
                raise PermissionError("User ID mismatch: access denied")

            logger.debug(
                "Internal user authorization successful for user '%s'",
                requested_user_id,
            )

        except PermissionError:
            # Re-raise permission errors
            raise
        except Exception as e:
            logger.warning("Could not verify internal user authorization: %s", e)
            # For security, fail closed - if we can't verify, deny access
            raise PermissionError("Authorization verification failed") from e
