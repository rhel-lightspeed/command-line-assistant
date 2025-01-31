"""Module that holds all the exceptions that can be raised by the dbus methods."""

from dasbus.error import DBusError, get_error_decorator

from command_line_assistant.dbus.constants import (
    CHAT_NAMESAPCE,
    ERROR_MAPPER,
    HISTORY_NAMESPACE,
    SERVICE_NAMESPACE,
)

#: Special decorator for mapping exceptions to dbus style exceptions
dbus_error = get_error_decorator(ERROR_MAPPER)


@dbus_error("NotAuthorizedUser", namespace=SERVICE_NAMESPACE)
class NotAuthorizedUser(DBusError):
    """The current user is not authenticated to issue queries."""


@dbus_error("RequestFailedError", namespace=CHAT_NAMESAPCE)
class RequestFailedError(DBusError):
    """Failed submit a request to the server."""


@dbus_error("CorruptedHistoryError", namespace=HISTORY_NAMESPACE)
class CorruptedHistoryError(DBusError):
    """History is corrupted and we can't do anything against it."""


@dbus_error("MissingHistoryFileError", namespace=HISTORY_NAMESPACE)
class MissingHistoryFileError(DBusError):
    """Missing history file in the destination"""


@dbus_error("HistoryNotAvailable", namespace=HISTORY_NAMESPACE)
class HistoryNotAvailable(DBusError):
    """History for that particular user is not available."""


@dbus_error("ChatNotFound", namespace=CHAT_NAMESAPCE)
class ChatNotFoundError(DBusError):
    """Couldn't find chat for the given user."""
