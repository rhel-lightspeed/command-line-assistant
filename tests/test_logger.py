import json
import logging
from unittest.mock import patch

import pytest

from command_line_assistant.logger import (
    EXTRAS_TO_SKIP,
    AuditFilter,
    AuditFormatter,
    NonAuditFilter,
    setup_daemon_logging,
)


def test_audit_formatter_format():
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
    record.user_id = "1000"

    audit_formatter = AuditFormatter()
    formatted = audit_formatter.format(record)
    data = json.loads(formatted)

    required_fields = [
        "priority",
        "message",
        "timestamp",
        "syslog_identifier",
        "code",
        "user_id",
        "audit_type",
        "level",
    ]
    for field in required_fields:
        assert field in data


@pytest.mark.parametrize(
    ("levelno", "expected"),
    (
        (50, 2),
        (40, 3),
        (30, 4),
        (20, 6),
        (10, 7),
        (100, 6),  # default to info
    ),
)
def test_get_syslog_priority_audit_formatter(levelno, expected):
    audit_formatter = AuditFormatter()
    assert audit_formatter._get_syslog_priority(levelno) == expected


@pytest.mark.parametrize(
    ("extras", "expected"),
    (
        ({"something": "yes"}, {"something": "yes"}),
        ({"user_id": "yes"}, {}),
        (
            {"args": "test", "exc_info": "test"},
            {},
        ),  # Test that some of the EXTRAS_TO_SKIP will work correctly.
    ),
)
def test_get_extra_fields(extras, expected):
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    for key, value in extras.items():
        setattr(record, key, value)

    audit_formatter = AuditFormatter()
    result = audit_formatter._get_extra_fields(record)
    assert result == expected


def test_get_extra_fields_with_skipping_values():
    """All of the EXTRAS_TO_SKIP values should be skipped properly"""
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    record.blabla = "test"

    for keys in EXTRAS_TO_SKIP:
        setattr(record, keys, "test")

    audit_formatter = AuditFormatter()
    result = audit_formatter._get_extra_fields(record)
    assert result == {"blabla": "test"}


@patch("logging.config.dictConfig")
def test_setup_logging(mock_dict_config, mock_config):
    """Test setup of logging configuration."""
    mock_config.logging.level = "INFO"
    setup_daemon_logging(mock_config)
    mock_dict_config.assert_called_once()


def test_audit_formatter_user_specific_logging():
    """Test user-specific logging configuration."""
    # Configure mock for user-specific settings
    formatter = AuditFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.user_id = "1000"
    record.something = "yes"

    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert data["user_id"] == "1000"
    assert "audit_data" in data
    assert data["audit_data"]["something"] == "yes"


def test_setup_logging_invalid_level_daemon(mock_config):
    """Test setup_logging with invalid log level."""
    mock_config.logging.level = "INVALID_LEVEL"
    with pytest.raises(ValueError):
        setup_daemon_logging(mock_config)


@pytest.mark.parametrize(
    ("audit", "expected"), ((True, True), (False, False), (None, False))
)
def test_audit_filter(audit, expected):
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.audit = audit

    assert AuditFilter().filter(record) == expected


@pytest.mark.parametrize(
    ("audit", "expected"), ((True, False), (False, True), (None, True))
)
def test_non_audit_filter(audit, expected):
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.audit = audit

    assert NonAuditFilter().filter(record) == expected
