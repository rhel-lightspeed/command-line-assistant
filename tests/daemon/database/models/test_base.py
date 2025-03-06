import uuid
from unittest import mock

import pytest
from sqlalchemy.engine.interfaces import Dialect

from command_line_assistant.daemon.database.models.base import GUID


def test_guid_process_bind_param_sqlite():
    dialect = Dialect()
    dialect.name = "sqlite"
    guid = GUID()

    # Test with None value
    assert guid.process_bind_param(None, dialect) is None

    # Test with UUID value
    uuid_value = uuid.uuid4().hex
    assert guid.process_bind_param(uuid_value, dialect) == uuid_value


def test_guid_process_bind_param_postgresql():
    dialect = Dialect()
    dialect.name = "postgresql"
    guid = GUID()

    # Test with None value
    assert guid.process_bind_param(None, dialect) is None

    # Test with UUID value
    uuid_value = str(uuid.uuid4())
    assert guid.process_bind_param(uuid_value, dialect) == uuid_value


@pytest.mark.parametrize(
    ("param_value", "expected_value"),
    (
        (
            "123e4567-e89b-12d3-a456-426655440000",
            uuid.UUID("123e4567-e89b-12d3-a456-426655440000"),
        ),
        (None, None),
        (
            uuid.UUID("123e4567-e89b-12d3-a456-426655440000"),
            uuid.UUID("123e4567-e89b-12d3-a456-426655440000"),
        ),
    ),
)
def test_guid_process_result_value(param_value, expected_value):
    dialect = Dialect()
    guid = GUID()

    assert guid.process_result_value(param_value, dialect) == expected_value


def test_guid_to_string_conversion():
    """Test GUID conversion to/from string"""
    guid = GUID()
    original_uuid = uuid.uuid4()
    str_uuid = str(original_uuid)

    dialect = Dialect()
    dialect.name = "postgresql"
    # Test conversion from UUID to string format
    assert guid.process_bind_param(original_uuid, dialect) == str_uuid

    # Test conversion from string back to UUID
    assert isinstance(guid.process_result_value(str_uuid, mock.Mock()), uuid.UUID)
