import copy
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from command_line_assistant import config, logger
from command_line_assistant.config import (
    BackendSchema,
    Config,
    HistorySchema,
    LoggingSchema,
    OutputSchema,
)
from command_line_assistant.config.schemas import AuthSchema
from command_line_assistant.logger import LOGGING_CONFIG_DICTIONARY
from tests.helpers import MockStream


@pytest.fixture(autouse=True)
def setup_logger(tmp_path, request):
    # This makes it so we can skip this using @pytest.mark.noautofixtures
    if "noautofixtures" in request.keywords:
        return

    logging_configuration = copy.deepcopy(LOGGING_CONFIG_DICTIONARY)
    logging_configuration["handlers"]["audit_file"]["filename"] = tmp_path / "audit.log"
    with patch(
        "command_line_assistant.logger.LOGGING_CONFIG_DICTIONARY", logging_configuration
    ):
        logger.setup_logging(config.Config(logging=config.LoggingSchema(level="DEBUG")))

        # get root logger
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)


@pytest.fixture
def mock_config(tmp_path):
    """Fixture to create a mock configuration"""
    cert_file = tmp_path / "cert.pem"
    key_file = tmp_path / "key.pem"
    history_file = tmp_path / "command-line-assistant" / "history.json"

    cert_file.write_text("cert")
    key_file.write_text("key")
    return Config(
        output=OutputSchema(
            enforce_script=False,
            file=Path("/tmp/test_output.txt"),
            prompt_separator="$",
        ),
        backend=BackendSchema(
            endpoint="http://test.endpoint/v1/query",
            auth=AuthSchema(cert_file=cert_file, key_file=key_file, verify_ssl=False),
        ),
        history=HistorySchema(enabled=True, file=history_file),
        logging=LoggingSchema(level="debug"),
    )


@pytest.fixture
def mock_dbus_session():
    """Create a mock DBus session."""
    return MagicMock()


@pytest.fixture
def mock_proxy():
    """Create a mock proxy for testing."""
    proxy = MagicMock()
    return proxy


@pytest.fixture
def mock_stream():
    return MockStream()


@pytest.fixture
def sample_history_data():
    """Create sample history data for testing."""
    return {
        "history": [
            {
                "id": "test-id",
                "timestamp": "2024-01-01T00:00:00Z",
                "interaction": {
                    "query": {"text": "test query", "role": "user"},
                    "response": {
                        "text": "test response",
                        "tokens": 2,
                        "role": "assistant",
                    },
                },
                "metadata": {
                    "session_id": "test-session",
                    "os_info": {
                        "distribution": "RHEL",
                        "version": "test",
                        "arch": "x86_64",
                    },
                },
            }
        ],
        "metadata": {
            "last_updated": "2024-01-01T00:00:00Z",
            "version": "0.1.0",
            "entry_count": 1,
            "size_bytes": 0,
        },
    }
