from pathlib import Path

import pytest

from command_line_assistant.config.schemas.database import DatabaseSchema


def test_database_schema_invalid_type():
    type = "NOT_FOUND_DB"
    with pytest.raises(
        ValueError, match="The database type must be one of .*, not NOT_FOUND_DB"
    ):
        DatabaseSchema(type=type)


@pytest.mark.parametrize(
    ("type", "port", "connection_string"),
    (
        ("sqlite", None, "sqlite:/test"),
        ("mysql", 3306, None),
        ("postgresql", 5432, None),
    ),
)
def test_database_schema_default_initialization(type, port, connection_string):
    result = DatabaseSchema(
        type=type, port=port, connection_string=connection_string, database="test"
    )

    assert result.port == port
    if connection_string:
        assert result.connection_string == Path(connection_string)
    assert result.type == type


@pytest.mark.parametrize(
    ("type", "expected"),
    (
        ("sqlite", None),
        ("mysql", 3306),
        ("postgresql", 5432),
    ),
)
def test_database_schema_initialization_no_port(type, expected):
    result = DatabaseSchema(type=type)
    assert result.port == expected
