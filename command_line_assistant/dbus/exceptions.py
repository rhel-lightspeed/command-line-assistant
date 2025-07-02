"""Module that holds all the exceptions that can be raised by the dbus methods."""

from dasbus.error import DBusError, get_error_decorator

from command_line_assistant.dbus.constants import (
    CHAT_NAMESPACE,
    ERROR_MAPPER,
    HISTORY_NAMESPACE,
)

#: Special decorator for mapping exceptions to dbus style exceptions
dbus_error = get_error_decorator(ERROR_MAPPER)


@dbus_error("RequestFailedError", namespace=CHAT_NAMESPACE)
class RequestFailedError(DBusError):
    """Failed submit a request to the server."""


@dbus_error("CorruptedHistoryError", namespace=HISTORY_NAMESPACE)
class CorruptedHistoryError(DBusError):
    """History is corrupted and we can't do anything against it."""


@dbus_error("MissingHistoryFileError", namespace=HISTORY_NAMESPACE)
class MissingHistoryFileError(DBusError):
    """Missing history file in the destination"""


@dbus_error("HistoryNotAvailableError", namespace=HISTORY_NAMESPACE)
class HistoryNotAvailableError(DBusError):
    """History for that particular user is not available."""


@dbus_error("HistoryNotEnabledError", namespace=HISTORY_NAMESPACE)
class HistoryNotEnabledError(DBusError):
    """History for that particular user is not enabled."""


@dbus_error("ChatNotFound", namespace=CHAT_NAMESPACE)
class ChatNotFoundError(DBusError):
    """Couldn't find chat for the given user."""
