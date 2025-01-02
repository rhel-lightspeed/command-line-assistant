"""Module for logging configuration."""

import copy
import json
import logging.config
from typing import Optional

from command_line_assistant.config import Config

LOGGING_CONFIG_DICTIONARY = {
    "version": 1,
    "disable_existing_loggers": False,
    "level": "DEBUG",
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s: %(message)s",
            "datefmt": "%m/%d/%Y %I:%M:%S %p",
        },
        "audit": {
            "()": "command_line_assistant.logger._create_audit_formatter",
            "config": None,  # Will be set in setup_logging
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "audit_file": {
            "class": "logging.FileHandler",
            "filename": "/var/log/audit/command-line-assistant.log",
            "formatter": "audit",
            "mode": "a",
        },
    },
    "loggers": {
        "root": {"handlers": ["console"], "level": "DEBUG"},
        "audit": {
            "handlers": ["audit_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
#: Define the dictionary configuration for the logger instance


class AuditFormatter(logging.Formatter):
    """Custom formatter that handles user-specific logging configuration."""

    def __init__(
        self, config: Config, fmt: Optional[str] = None, datefmt: Optional[str] = None
    ):
        """Initialize the formatter with config.

        Args:
            config (Config): The application configuration
            fmt (Optional[str], optional): Format string. Defaults to None.
            datefmt (Optional[str], optional): Date format string. Defaults to None.
        """
        super().__init__(fmt, datefmt)
        self._config = config

    def format(self, record: logging.LogRecord) -> str:
        """Format the record based on user-specific settings.

        Args:
            record (logging.LogRecord): The log record to format

        Note:
            This method is called by the logging framework to format the log message.

        Example:
            This is how it will look like in the audit.log file::

            >>> # In case the query and response are disabled for the current user.
            >>> {"timestamp":"2025-01-03T11:26:37.%fZ","user":"my-user","message":"Query executed successfully.","query":null,"response":null}

            >>> # In case the query and response are enabled for the current user.
            >>> {"timestamp":"2025-01-03T11:26:37.%fZ","user":"my-user","message":"Query executed successfully.","query":"My query!","response":"My super response"}

        Returns:
            str: The formatted log message
        """
        # Basic structure that will always be included
        data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "user": getattr(record, "user", "unknown"),
            "message": record.getMessage(),
        }

        is_query_enabled = hasattr(
            record, "query"
        ) and self._config.logging.should_log_for_user(data["user"], "question")
        # Add query if enabled for user
        data["query"] = record.query if is_query_enabled else None  # type: ignore

        is_response_enabled = hasattr(
            record, "response"
        ) and self._config.logging.should_log_for_user(data["user"], "responses")
        # Add response if enabled for user
        data["response"] = record.response if is_response_enabled else None  # type: ignore

        # separators will remove whitespace between items
        # ensure_ascii will properly handle unicode characters.
        return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _create_audit_formatter(config: Config) -> AuditFormatter:
    """Internal method to create a new audit formatter instance.

    Args:
        config (Config): The application configuration

    Returns:
        AuditFormatter: The new audit formatter instance.
    """

    fmt = '{"timestamp": "%(asctime)s", "user": "%(user)s", "message": "%(message)s"%(query)s%(response)s}'
    datefmt = "%Y-%m-%dT%H:%M:%S.%fZ"
    return AuditFormatter(config=config, fmt=fmt, datefmt=datefmt)


def setup_logging(config: Config):
    """Setup basic logging functionality"

    Args:
        config (Config): Instance of a config class.
    """

    logging_configuration = copy.deepcopy(LOGGING_CONFIG_DICTIONARY)
    logging_configuration["loggers"]["root"]["level"] = config.logging.level
    # Set the config in the formatter
    logging_configuration["formatters"]["audit"]["config"] = config

    logging.config.dictConfig(logging_configuration)
