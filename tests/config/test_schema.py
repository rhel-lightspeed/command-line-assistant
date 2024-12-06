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
