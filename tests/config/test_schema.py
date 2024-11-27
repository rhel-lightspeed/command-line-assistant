import pytest

from command_line_assistant import config


@pytest.mark.parametrize(
    ("schema",),
    (
        (config.LoggingSchema,),
        (config.OutputSchema,),
        (config.BackendSchema,),
        (config.HistorySchema,),
    ),
)
def test_initialize_schemas(schema):
    # Making sure that we don't error out while initializing the schema with default vlaues.
    assert isinstance(schema(), schema)
