"""D-Bus constants"""

from dasbus.connection import SystemMessageBus
from dasbus.error import ErrorMapper
from dasbus.identifier import DBusServiceIdentifier

#: Instance of error mapping to allow d-bus to serialize exceptions.
ERROR_MAPPER: ErrorMapper = ErrorMapper()

#: System bus with error mapping to serialize exceptions.
SYSTEM_BUS: SystemMessageBus = SystemMessageBus(error_mapper=ERROR_MAPPER)

#: The base-level service namespace
SERVICE_NAMESPACE = ("com", "redhat", "lightspeed")

#: The query namespace
QUERY_NAMESAPCE = (*SERVICE_NAMESPACE, "query")

#: The history namespace
HISTORY_NAMESPACE = (*SERVICE_NAMESPACE, "history")

#: The query identifier that represents a dbus service
QUERY_IDENTIFIER = DBusServiceIdentifier(
    namespace=QUERY_NAMESAPCE, message_bus=SYSTEM_BUS
)

#: The history identifier that represents a dbus service
HISTORY_IDENTIFIER = DBusServiceIdentifier(
    namespace=HISTORY_NAMESPACE, message_bus=SYSTEM_BUS
)
