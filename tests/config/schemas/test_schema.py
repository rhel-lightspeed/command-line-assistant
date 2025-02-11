import pytest

from command_line_assistant.config.schemas.backend import AuthSchema, BackendSchema
from command_line_assistant.config.schemas.database import DatabaseSchema
from command_line_assistant.config.schemas.history import HistorySchema
from command_line_assistant.config.schemas.logging import LoggingSchema


@pytest.mark.parametrize(
    ("schema",),
    (
        (LoggingSchema,),
        (BackendSchema,),
        (HistorySchema,),
        (AuthSchema,),
        (DatabaseSchema,),
    ),
)
def test_initialize_schemas_default_values(schema):
    # Making sure that we don't error out while initializing the schema with default values.
    assert isinstance(schema(), schema)
