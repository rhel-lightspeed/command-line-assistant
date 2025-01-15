from command_line_assistant.dbus.context import (
    DaemonContext,
)


def test_daemon_context_config_property(mock_config):
    context = DaemonContext(mock_config)
    assert context.config == mock_config
