from dasbus.connection import SystemMessageBus
from dasbus.error import ErrorMapper
from dasbus.identifier import DBusServiceIdentifier

ERROR_MAPPER = ErrorMapper()

SYSTEM_BUS = SystemMessageBus(error_mapper=ERROR_MAPPER)

SERVICE_NAMESPACE = ("com", "redhat", "lightspeed")

QUERY_NAMESAPCE = (*SERVICE_NAMESPACE, "query")
HISTORY_NAMESPACE = (*SERVICE_NAMESPACE, "history")

# Define the service identifier for a query
QUERY_IDENTIFIER = DBusServiceIdentifier(
    namespace=QUERY_NAMESAPCE, message_bus=SYSTEM_BUS
)
# Define the service identifier for a history
HISTORY_IDENTIFIER = DBusServiceIdentifier(
    namespace=HISTORY_NAMESPACE, message_bus=SYSTEM_BUS
)
