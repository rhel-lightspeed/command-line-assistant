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
        # Mock the authorization method to bypass D-Bus calls in tests
        with patch.object(
            user_interface, "_get_caller_unix_user_id", return_value=1000
        ):
            result = user_interface.GetUserId(1000)
            assert result == "4d465f1c-0507-5dfa-9ea0-e2de1a9e90a5"


def test_get_user_id_returns_same_id_for_same_user(user_interface, tmp_path):
    """Test that get_user_id returns the same ID for the same effective user ID"""
    machine_id = tmp_path / "machine-id"
    machine_id.write_text("09e28913cb074ed995a239c93b07fd8a")
    with patch("command_line_assistant.daemon.session.MACHINE_ID_PATH", machine_id):
        # Mock the authorization method to return the requested user ID (simulating authorized access)
        def mock_get_caller_unix_user_id(sender):
            # This mock simulates that the caller is authorized for the user ID they're requesting
            # In the real implementation, this would verify the actual caller's Unix user ID
            return 1000 if sender else 1000  # Default to 1000 for test

        with patch.object(
            user_interface,
            "_get_caller_unix_user_id",
            side_effect=mock_get_caller_unix_user_id,
        ):
            id1 = user_interface.GetUserId(1000)
            id2 = user_interface.GetUserId(1000)
            assert id1 == id2

            # For testing different user ID, we need to mock a different caller
            def mock_get_caller_unix_user_id_1001(sender):
                return 1001

            with patch.object(
                user_interface,
                "_get_caller_unix_user_id",
                side_effect=mock_get_caller_unix_user_id_1001,
            ):
                id3 = user_interface.GetUserId(1001)
                assert id1 != id3
