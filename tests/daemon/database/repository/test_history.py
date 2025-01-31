from uuid import UUID

import pytest

from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.repository.history import HistoryRepository


def test_history_repository_initialization(mock_config):
    try:
        HistoryRepository(DatabaseManager(mock_config))
    except Exception as e:
        pytest.fail(f"initialization raised {e} unexpectedly!")


def test_select_by_chat_id(mock_config):
    repository = HistoryRepository(DatabaseManager(mock_config))
    uid = "7782e922-dffb-11ef-bdf5-52b437312584"
    repository.insert({"user_id": uid, "chat_id": uid})

    result = repository.select_by_chat_id(uid)
    assert result.chat_id == UUID(uid)  # type: ignore


def test_select_all_history(mock_config):
    repository = HistoryRepository(DatabaseManager(mock_config))
    uid = "7782e922-dffb-11ef-bdf5-52b437312584"
    uid2 = "4d7628be-dffc-11ef-a5b8-52b437312584"
    repository.insert({"user_id": uid, "chat_id": uid})
    repository.insert({"user_id": uid, "chat_id": uid2})

    result = repository.select_all_history(uid)
    assert len(result) == 2


def test_delete_all(mock_config):
    repository = HistoryRepository(DatabaseManager(mock_config))
    uid = "7782e922-dffb-11ef-bdf5-52b437312584"
    uid2 = "4d7628be-dffc-11ef-a5b8-52b437312584"
    repository.insert({"user_id": uid, "chat_id": uid})
    repository.insert({"user_id": uid, "chat_id": uid2})

    repository.delete_all(uid)
    result = repository.select_all_history(uid)
    assert len(result) == 0
