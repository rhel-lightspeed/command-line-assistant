from dasbus.connection import SessionMessageBus
from dasbus.error import ErrorMapper
from dasbus.identifier import DBusServiceIdentifier

ERROR_MAPPER = ErrorMapper()

SESSION_BUS = SessionMessageBus(error_mapper=ERROR_MAPPER)

SERVICE_NAMESPACE = ("com", "redhat", "lightspeed")

# Define the service identifier for a query
SERVICE_IDENTIFIER = DBusServiceIdentifier(
    namespace=SERVICE_NAMESPACE, message_bus=SESSION_BUS
)
