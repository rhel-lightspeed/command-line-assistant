import logging

from dasbus.loop import EventLoop

from command_line_assistant.config import Config
from command_line_assistant.dbus.constants import SERVICE_IDENTIFIER, SESSION_BUS
from command_line_assistant.dbus.definitions import ProcessContext, QueryInterface


def serve(config: Config):
    # TODO(r0x0d): Only makes sense if we are in debug mode.
    # Print the generated XML specification.
    # print(XMLGenerator.prettify_xml(QueryInterface.__dbus_xml__))

    logging.info("Starting clad!")

    try:
        # TODO(r0x0d): Add the authentication info here later
        process_context = ProcessContext(config=config)

        # Publish the instance at /org/example/HelloWorld.
        SESSION_BUS.publish_object(
            SERVICE_IDENTIFIER.object_path, QueryInterface(process_context)
        )

        # Register the service name org.example.HelloWorld.
        SESSION_BUS.register_service(SERVICE_IDENTIFIER.service_name)

        # Start the event loop.
        loop = EventLoop()
        loop.run()
    finally:
        # Unregister the DBus service and objects.
        SESSION_BUS.disconnect()
