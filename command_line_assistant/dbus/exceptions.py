from dasbus.error import DBusError, get_error_decorator

from command_line_assistant.dbus.constants import (
    ERROR_MAPPER,
    HISTORY_NAMESPACE,
    QUERY_NAMESAPCE,
    SERVICE_NAMESPACE,
)

# The decorator for DBus errors.
dbus_error = get_error_decorator(ERROR_MAPPER)


@dbus_error("NotAuthorizedUser", namespace=SERVICE_NAMESPACE)
class NotAuthorizedUser(DBusError):
    """The current user is not authenticated to issue queries."""


@dbus_error("RequestFailedError", namespace=QUERY_NAMESAPCE)
class RequestFailedError(DBusError):
    """Failed submit a request to the server."""


@dbus_error("CorruptedHistoryError", namespace=HISTORY_NAMESPACE)
class CorruptedHistoryError(DBusError):
    """History is corrupted and we can't do anything against it."""


@dbus_error("MissingHistoryFileError", namespace=HISTORY_NAMESPACE)
class MissingHistoryFileError(DBusError):
    """Missing history file in the destination"""
