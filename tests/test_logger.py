import json
import logging
from unittest.mock import patch

import pytest

from command_line_assistant.logger import (
    AuditFormatter,
    _create_audit_formatter,
    _should_log_for_user,
    setup_logging,
)


@pytest.fixture
def audit_formatter(mock_config):
    """Create an AuditFormatter instance."""
    return AuditFormatter(config=mock_config)


def test_audit_formatter_format(audit_formatter):
    """Test basic formatting of log records."""
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.user = "testuser"

    formatted = audit_formatter.format(record)
    data = json.loads(formatted)

    assert "timestamp" in data
    assert data["user"] == "testuser"
    assert data["message"] == "Test message"
    assert data["query"] is None
    assert data["response"] is None


def test_audit_formatter_with_query_and_response(audit_formatter):
    """Test formatting with query and response fields."""
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.user = "testuser"
    record.query = "test query"
    record.response = "test response"

    formatted = audit_formatter.format(record)
    data = json.loads(formatted)

    assert data["query"] == "test query"
    assert data["response"] == "test response"


def test_create_audit_formatter(mock_config):
    """Test creation of audit formatter."""
    formatter = _create_audit_formatter(mock_config)
    assert isinstance(formatter, AuditFormatter)


@patch("logging.config.dictConfig")
def test_setup_logging(mock_dict_config, mock_config):
    """Test setup of logging configuration."""
    mock_config.logging.level = "INFO"
    setup_logging(mock_config)
    mock_dict_config.assert_called_once()


def test_audit_formatter_user_specific_logging(mock_config):
    """Test user-specific logging configuration."""
    # Configure mock for user-specific settings
    formatter = AuditFormatter(config=mock_config)

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.user = "1000"
    record.query = "test query"
    record.response = "test response"

    formatted = formatter.format(record)
    data = json.loads(formatted)

    # Query should be included but response should not for this user
    assert data["query"] == "test query"
    assert data["response"] is None


def test_setup_logging_invalid_level(mock_config):
    """Test setup_logging with invalid log level."""
    mock_config.logging.level = "INVALID_LEVEL"
    with pytest.raises(ValueError):
        setup_logging(mock_config)


@pytest.mark.parametrize(
    ("users", "effective_user_id", "log_type", "expected"),
    (
        ({"1000": {"response": True, "question": False}}, 1000, "response", True),
        ({"1000": {"response": False, "question": False}}, 1000, "response", False),
        ({"1000": {"response": False, "question": True}}, 1000, "question", True),
        ({"1000": {"response": False, "question": False}}, 1000, "question", False),
        # User is defined in the config, but nothing is specified
        ({"1000": {}}, 1000, "question", False),
        ({"1000": {}}, 1000, "response", False),
        ({"1000": {}, "1001": {"response": True}}, 1001, "response", True),
        ({"1000": {}, "1001": {"question": True}}, 1001, "question", True),
        ({"1000": {}, "1001": {}}, 1001, "question", False),
    ),
)
def test_should_log_for_user(users, effective_user_id, log_type, expected, mock_config):
    mock_config.logging.users = users
    assert _should_log_for_user(effective_user_id, mock_config, log_type) == expected
