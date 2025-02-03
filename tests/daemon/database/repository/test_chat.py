from uuid import UUID

import pytest

from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.repository.chat import ChatRepository


def test_chat_repository_initialization(mock_config):
    try:
        ChatRepository(DatabaseManager(mock_config))
    except Exception as e:
        pytest.fail(f"initialization raised {e} unexpectedly!")


def test_select_latest_chat(mock_config):
    repository = ChatRepository(DatabaseManager(mock_config))
    uid = "7782e922-dffb-11ef-bdf5-52b437312584"
    repository.insert({"user_id": uid, "name": "test", "description": "test"})

    result = repository.select_latest_chat(uid)
    assert result.name == "test"  # type: ignore
    assert result.user_id == UUID(uid)  # type: ignore
