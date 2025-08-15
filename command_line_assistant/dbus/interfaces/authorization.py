"""D-Bus authorization mixin for interface classes."""

import logging
from functools import wraps
from typing import Callable

from command_line_assistant.daemon.session import UserSessionManager
from command_line_assistant.dbus.sender_context import get_current_sender

logger = logging.getLogger(__name__)


def require_user_authorization(user_id_param: str = "user_id") -> Callable:
    """Decorator to verify that the sender is authorized to access the requested
    user's data.

    Arguments:
        user_id_param (str): The name of the parameter containing the user ID to
        verify. Defaults to "user_id".

    Returns:
        Callable: The decorated method with authorization verification.

    Raises:
        PermissionError: If the sender's user ID doesn't match the requested
        user ID.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get the user_id from the method arguments
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()

            if user_id_param not in bound_args.arguments:
                raise ValueError(
                    f"Method {func.__name__} must have a '{user_id_param}' parameter"
                )

            requested_user_id = bound_args.arguments[user_id_param]

            # Perform authorization check
            sender = get_current_sender()

            # If the type of the user_id_param is an int, call verify_unix_user_authorization.
            # Otherwise, call verify_internal_user_authorization
            if isinstance(requested_user_id, int):
                self._verify_unix_user_authorization(sender, requested_user_id)
            else:
                self._verify_internal_user_authorization(
                    sender, requested_user_id, self._session_manager
                )

            # If authorization passes, call the original method
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class DBusAuthorizationMixin:
    """Mixin class providing D-Bus caller authorization functionality."""

    def _get_sender_unix_user_id(self, sender: str) -> int:
        """Get the Unix user ID of the D-Bus sender.

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
        """Verify that the sender's Unix user ID matches the requested Unix user
        ID.

        Arguments:
            sender: The D-Bus sender.
            requested_unix_user_id (int): The Unix user ID being requested.

        Raises:
            PermissionError: If the caller's Unix user ID doesn't match the requested user ID.
        """
        try:
            sender_unix_id = self._get_sender_unix_user_id(sender)

            # Reject the request if the Unix user ID of the sender is different
            # from the Unix user ID being requested.
            if requested_unix_user_id != sender_unix_id:
                logger.warning(
                    "Authorization failed: caller Unix user ID '%d' does not match requested Unix user ID '%d'",
                    sender_unix_id,
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
        self, sender: str, requested_user_id: str, session_manager: UserSessionManager
    ) -> None:
        """Verify that the sender's user UUID matches the requested user UUID.

        Arguments:
            sender: The D-Bus sender.
            requested_user_id (str): The internal user UUID being requested.
            session_manager: UserSessionManager instance for user ID conversion.

        Raises:
            PermissionError: If the sender's user UUID doesn't match the requested user UUID.
        """
        try:
            sender_unix_id = self._get_sender_unix_user_id(sender)
            # Convert UNIX user ID to our internal user ID format
            sender_internal_id = session_manager.get_user_id(sender_unix_id)

            # Reject the request if the internal user ID of the caller is different
            # from the internal user ID being requested
            if requested_user_id != sender_internal_id:
                logger.warning(
                    "Authorization failed: sender's user UUID '%s' does not match requested user UUID '%s'",
                    sender_internal_id,
                    requested_user_id,
                    extra={"audit": True},
                )
                raise PermissionError("User UUID mismatch: access denied")

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
