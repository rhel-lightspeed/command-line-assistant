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


def test_backend_schema_with_auth_dict():
    """Test BackendSchema initialization with auth as dict"""
    auth_dict = {
        "cert_file": "/path/to/cert.pem",
        "key_file": "/path/to/key.pem",
        "verify_ssl": False,
    }

    schema = BackendSchema(
        endpoint="https://api.example.com", auth=AuthSchema(**auth_dict)
    )

    assert isinstance(schema.auth, AuthSchema)
    assert str(schema.auth.cert_file) == "/path/to/cert.pem"
    assert str(schema.auth.key_file) == "/path/to/key.pem"
    assert schema.auth.verify_ssl is False
