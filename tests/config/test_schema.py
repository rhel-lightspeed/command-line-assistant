from pathlib import Path

import pytest

from command_line_assistant.config import schemas


@pytest.mark.parametrize(
    ("schema",),
    (
        (schemas.LoggingSchema,),
        (schemas.OutputSchema,),
        (schemas.BackendSchema,),
        (schemas.HistorySchema,),
        (schemas.AuthSchema,),
        (schemas.DatabaseSchema,),
    ),
)
def test_initialize_schemas(schema):
    # Making sure that we don't error out while initializing the schema with default vlaues.
    assert isinstance(schema(), schema)


def test_logging_schema_invalid_level():
    level = "NOT_FOUND"

    with pytest.raises(
        ValueError, match="The requested level 'NOT_FOUND' is not allowed."
    ):
        schemas.LoggingSchema(level=level)


def test_database_schema_invalid_type():
    type = "NOT_FOUND_DB"
    with pytest.raises(
        ValueError, match="The database type must be one of .*, not NOT_FOUND_DB"
    ):
        schemas.DatabaseSchema(type=type)


@pytest.mark.parametrize(
    ("type", "port", "connection_string"),
    (
        ("sqlite", None, "sqlite:/test"),
        ("mysql", 3306, None),
        ("postgresql", 5432, None),
    ),
)
def test_database_schema_default_initialization(type, port, connection_string):
    result = schemas.DatabaseSchema(
        type=type, port=port, connection_string=connection_string, database="test"
    )

    assert result.port == port
    if connection_string:
        assert result.connection_string == Path(connection_string)
    assert result.type == type
