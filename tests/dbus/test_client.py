import pytest

from command_line_assistant.dbus.client import DbusClient


def test_initialize_dbus_utils(mock_dbus_service):
    dbus = DbusClient()

    try:
        assert dbus.chat_proxy
        assert dbus.history_proxy
        assert dbus.user_proxy
    except Exception as e:
        pytest.fail(f"Failed to get proxy: {str(e)}")
