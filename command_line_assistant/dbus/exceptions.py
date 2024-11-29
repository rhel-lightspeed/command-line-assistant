from dasbus.error import DBusError, get_error_decorator

from command_line_assistant.dbus.constants import ERROR_MAPPER, SERVICE_NAMESPACE

# The decorator for DBus errors.
dbus_error = get_error_decorator(ERROR_MAPPER)


@dbus_error("NotAuthorizedUser", namespace=SERVICE_NAMESPACE)
class NotAuthorizedUser(DBusError):
    """The current user is not authenticated to issue queries."""

    pass


@dbus_error("FailedToGetResponse", namespace=SERVICE_NAMESPACE)
class FailedToGetResponse(DBusError):
    """Failed to get a response from backend."""

    pass
