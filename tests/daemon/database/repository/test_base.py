import uuid
from datetime import datetime

import pytest
from sqlalchemy import Column, Row, Text

from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.models.base import BaseModel
from command_line_assistant.daemon.database.repository.base import BaseRepository


class BaseMockModel(BaseModel):
    __tablename__ = "base"

    name = Column(Text)
    user_id = Column(Text, default="1")


def test_base_repository_initialization(mock_config):
    try:
        BaseRepository(DatabaseManager(mock_config), model=BaseMockModel)
    except Exception as e:
        pytest.fail(f"initialization raised {e} unexpectedly!")


@pytest.fixture
def base_repository(mock_config):
    return BaseRepository(DatabaseManager(mock_config), model=BaseMockModel)


def test_insert(base_repository):
    result = base_repository.insert({"name": "test"})
    assert isinstance(result, Row)
    assert isinstance(result[0], uuid.UUID)


def test_select(base_repository):
    # add data for select
    base_repository.insert({"name": "test"})

    result = base_repository.select()

    assert len(result) == 1
    assert result[0].name == "test"


def test_select_deleted_at_set(base_repository):
    # add data for select
    base_repository.insert({"name": "test", "deleted_at": datetime.now()})

    result = base_repository.select()
    assert len(result) == 0


def test_select_all_by_id(base_repository):
    # add data for select
    inserted = base_repository.insert({"name": "test"})
    result = base_repository.select_all_by_id(inserted[0])
    assert len(result) == 1
    assert result[0].id == inserted[0]


def test_select_all_by_user_id(base_repository):
    # add data for select
    inserted = base_repository.insert(
        {"name": "test", "user_id": "52fbc710-dffe-11ef-9ee3-52b437312584"}
    )
    result = base_repository.select_all_by_user_id(
        "52fbc710-dffe-11ef-9ee3-52b437312584"
    )
    assert len(result) == 1
    assert result[0].id == inserted[0]


def test_select_first(base_repository):
    # add data for select
    first = base_repository.insert({"name": "test"})
    base_repository.insert(
        {"name": "test", "user_id": "52fbc710-dffe-11ef-9ee3-52b437312584"}
    )
    result = base_repository.select_first()
    assert len(result) == 1
    assert result[0].id == first[0]


def test_select_by_id(base_repository):
    # add data for select
    first = base_repository.insert({"name": "test"})
    base_repository.insert(
        {"name": "test", "user_id": "52fbc710-dffe-11ef-9ee3-52b437312584"}
    )
    result = base_repository.select_by_id(first[0])
    assert len(result) == 1
    assert result[0].id == first[0]


def test_select_by_name(base_repository):
    # add data for select
    base_repository.insert({"name": "test"})
    base_repository.insert(
        {"name": "test2", "user_id": "52fbc710-dffe-11ef-9ee3-52b437312584"}
    )
    result = base_repository.select_by_name(
        "52fbc710-dffe-11ef-9ee3-52b437312584", "test2"
    )
    assert len(result) == 1
    assert result[0].name != "test"


def test_update(base_repository):
    # add data for select
    inserted = base_repository.insert({"name": "test"})

    base_repository.update({"name": "updated"}, inserted[0])

    result = base_repository.select_by_id(inserted[0])
    assert result[0].name == "updated"
    assert result[0].name != "test"


def test_delete(base_repository):
    # add data for select
    inserted = base_repository.insert({"name": "test"})

    base_repository.delete(inserted[0])

    result = base_repository.select_by_id(inserted[0])
    assert not result
