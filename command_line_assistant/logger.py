"""Module for logging configuration."""

import copy
import json
import logging.config
from logging import LogRecord
from typing import Any, Optional

from command_line_assistant.config import Config

#: Define the dictionary configuration for the logger instance
LOGGING_CONFIG_DICTIONARY = {
    "version": 1,
    "disable_existing_loggers": False,
    "level": "INFO",
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s: %(message)s",
            "datefmt": "%m/%d/%Y %I:%M:%S %p",
        },
        "audit": {
            "()": "command_line_assistant.logger.AuditFormatter",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
            "format": "[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s: %(message)s",
        },
    },
    "filters": {
        "audit_only": {
            "()": "command_line_assistant.logger.AuditFilter",
        },
        "non_audit_only": {
            "()": "command_line_assistant.logger.NonAuditFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
            "filters": ["non_audit_only"],
        },
        "audit": {
            "class": "logging.StreamHandler",
            "formatter": "audit",
            "stream": "ext://sys.stdout",
            "filters": ["audit_only"],
        },
    },
    "loggers": {
        # Root logger
        "root": {"handlers": ["audit", "console"], "level": "INFO"},
    },
}

#: Set of keys to skip during auditting. If any of those needs to be in the
#: audit log, simply remove them from this list.
EXTRAS_TO_SKIP = (
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "taskName",
    "module",
    "server",
    "thread",
    "process",
    "processName",
    "msecs",
    "msg",
    "name",
    "pathname",
    "relativeCreated",
    "stack_info",
    "threadName",
    "audit",
    "user_id",
)


class AuditFilter(logging.Filter):
    """Filter to separate audit logs from regular logs."""

    def filter(self, record: LogRecord) -> bool:
        """Filter records based on the presence of audit attribute.

        Args:
            record (LogRecord): The log record to check

        Returns:
            bool: True if the record should be processed, False otherwise
        """
        return bool(getattr(record, "audit", False))


class NonAuditFilter(logging.Filter):
    """Filter to separate regular logs from audit logs."""

    def filter(self, record: LogRecord) -> bool:
        """Filter records based on the absence of audit attribute.

        Args:
            record (LogRecord): The log record to check

        Returns:
            bool: True if the record should be processed, False otherwise
        """
        return not bool(getattr(record, "audit", False))


class AuditFormatter(logging.Formatter):
    """Custom formatter that handles user-specific logging configuration."""

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        """Initialize the formatter with config.

        Args:
            config (Config): The application configuration
            fmt (Optional[str], optional): Format string. Defaults to None.
            datefmt (Optional[str], optional): Date format string. Defaults to None.
        """
        super().__init__(fmt, datefmt)

    def format(self, record: LogRecord) -> str:
        """Format the record as JSON for journald consumption.

        Args:
            record (logging.LogRecord): The log record to format

        Returns:
            str: JSON formatted log message
        """
        user_id = getattr(record, "user_id", None)

        # Build base structured data
        structured_data = {
            "priority": self._get_syslog_priority(record.levelno),
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
            "syslog_identifier": "command-line-assistant",
            "code": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            },
            "user_id": user_id,
            "audit_type": "command-line-assistant-audit",
            "level": record.levelname,
        }

        # Add any additional fields from record
        extras = self._get_extra_fields(record)
        if extras:
            structured_data["audit_data"] = extras

        return json.dumps(structured_data, default=str)

    def _get_syslog_priority(self, levelno: int) -> int:
        """Convert Python logging levels to syslog priorities.

        Args:
            levelno (int): Python logging level number

        Returns:
            int: Corresponding syslog priority
        """
        priorities = {
            logging.CRITICAL: 2,  # LOG_CRIT
            logging.ERROR: 3,  # LOG_ERR
            logging.WARNING: 4,  # LOG_WARNING
            logging.INFO: 6,  # LOG_INFO
            logging.DEBUG: 7,  # LOG_DEBUG
        }
        return priorities.get(levelno, 6)  # Default to INFO

    def _get_extra_fields(self, record: LogRecord) -> dict[str, Any]:
        """Extract additional fields from the record.

        Args:
            record (LogRecord): The log record

        Returns:
            dict[str, Any]: Dictionary of extra fields
        """
        extras = {}
        for key, value in record.__dict__.items():
            if key not in EXTRAS_TO_SKIP:
                extras[key] = value
        return extras


def setup_logging(config: Optional[Config] = None) -> None:
    """Setup basic logging functionality.

    Note:
        This is intended to be called by the daemon to initialize their logging routine.

    Arguments:
        config (Config): Instance of a config class.
    """
    logging_configuration = copy.deepcopy(LOGGING_CONFIG_DICTIONARY)
    loggin_level = "DEBUG" if not config else config.logging.level
    logging_configuration["loggers"]["root"]["level"] = loggin_level
    logging.config.dictConfig(logging_configuration)
