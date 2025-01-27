import pytest

from command_line_assistant.config.schemas.logging import LoggingSchema


def test_logging_schema_invalid_level():
    level = "NOT_FOUND"

    with pytest.raises(
        ValueError, match="The requested level 'NOT_FOUND' is not allowed."
    ):
        LoggingSchema(level=level)


def test_logging_user_not_in_system():
    with pytest.raises(
        ValueError,
        match="test is not present on the system. Remove it from the configuration.",
    ):
        LoggingSchema(
            level="INFO", users={"test": {"response": True, "question": True}}
        )
