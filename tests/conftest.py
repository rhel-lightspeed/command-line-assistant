import logging
from pathlib import Path

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


@pytest.fixture(autouse=True)
def setup_logger(request):
    # This makes it so we can skip this using @pytest.mark.noautofixtures
    if "noautofixtures" in request.keywords:
        return

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
        history=HistorySchema(
            enabled=True, file=Path("/tmp/test_history.json"), max_size=100
        ),
        logging=LoggingSchema(level="debug"),
    )
