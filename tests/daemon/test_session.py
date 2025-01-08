import uuid
from unittest.mock import patch

import pytest

from command_line_assistant.daemon.session import UserSessionManager


def test_initialize_user_session_manager():
    session = UserSessionManager("1000")
    assert session._effective_user == "1000"
    assert not session._machine_uuid
    assert not session._session_uuid


def test_read_machine_id(tmp_path):
    machine_id = tmp_path / "machine-id"
    machine_id.write_text("09e28913cb074ed995a239c93b07fd8a")
    with patch("command_line_assistant.daemon.session.MACHINE_ID_PATH", machine_id):
        session = UserSessionManager("1000")
        assert session.machine_id == uuid.UUID("09e28913cb074ed995a239c93b07fd8a")


def test_generate_session_id(tmp_path):
    machine_id = tmp_path / "machine-id"
    machine_id.write_text("09e28913cb074ed995a239c93b07fd8a")
    with patch("command_line_assistant.daemon.session.MACHINE_ID_PATH", machine_id):
        session = UserSessionManager("1000")
        assert session.session_id == uuid.UUID("4d465f1c-0507-5dfa-9ea0-e2de1a9e90a5")


def test_generate_session_id_twice(tmp_path):
    """This verifies that the session ID is generated only once."""
    machine_id = tmp_path / "machine-id"
    machine_id.write_text("09e28913cb074ed995a239c93b07fd8a")
    with patch("command_line_assistant.daemon.session.MACHINE_ID_PATH", machine_id):
        session = UserSessionManager("1000")
        assert session.session_id == uuid.UUID("4d465f1c-0507-5dfa-9ea0-e2de1a9e90a5")

        session = UserSessionManager("1000")
        assert session.session_id == uuid.UUID("4d465f1c-0507-5dfa-9ea0-e2de1a9e90a5")


@pytest.mark.parametrize(
    ("machine_id", "effective_user_id", "expected"),
    (
        (
            "09e28913cb074ed995a239c93b07fd8a",
            "1000",
            "4d465f1c-0507-5dfa-9ea0-e2de1a9e90a5",
        ),
        # Different user on the same machine.
        (
            "09e28913cb074ed995a239c93b07fd8a",
            "1001",
            "9f522470-d57d-55e2-8f74-b90b19830e9d",
        ),
        # Same effective user id, but in a different machine
        (
            "771640198a6344bba7ad356cf525243a",
            "1000",
            "b4e5eb85-c750-5130-bd72-851e531e73c3",
        ),
    ),
)
def test_generate_session_id_different_users(
    tmp_path, machine_id, effective_user_id, expected
):
    machine_id_file = tmp_path / "machine-id"
    machine_id_file.write_text(machine_id)
    with patch(
        "command_line_assistant.daemon.session.MACHINE_ID_PATH", machine_id_file
    ):
        session = UserSessionManager(effective_user_id)
        assert session.session_id == uuid.UUID(expected)


def test_empty_machine_id_file(tmp_path):
    machine_id_file = tmp_path / "machine-id"
    machine_id_file.write_text("")
    with patch(
        "command_line_assistant.daemon.session.MACHINE_ID_PATH", machine_id_file
    ):
        session = UserSessionManager("1000")
        with pytest.raises(ValueError, match="Machine ID at .* is empty"):
            assert session.machine_id


def test_machine_id_file_not_found(tmp_path):
    machine_id_file = tmp_path / "test" / "machine-id"
    with patch(
        "command_line_assistant.daemon.session.MACHINE_ID_PATH", machine_id_file
    ):
        session = UserSessionManager("1000")
        with pytest.raises(FileNotFoundError, match="Machine ID file not found at .*"):
            assert session.machine_id
