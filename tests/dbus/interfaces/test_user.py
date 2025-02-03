from unittest.mock import patch

import pytest
from dasbus.server.template import InterfaceTemplate

from command_line_assistant.dbus.interfaces.user import UserInterface


@pytest.fixture
def user_interface(mock_context):
    """Create a QueryInterface instance with mock implementation."""
    interface = UserInterface(mock_context)
    assert isinstance(interface, InterfaceTemplate)
    return interface


def test_get_user_id(user_interface, tmp_path):
    machine_id = tmp_path / "machine-id"
    machine_id.write_text("09e28913cb074ed995a239c93b07fd8a")
    with patch("command_line_assistant.daemon.session.MACHINE_ID_PATH", machine_id):
        result = user_interface.GetUserId(1000)
        assert result == "4d465f1c-0507-5dfa-9ea0-e2de1a9e90a5"
