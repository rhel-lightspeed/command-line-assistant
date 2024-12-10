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
def mock_config():
    """Fixture to create a mock configuration"""
    return Config(
        output=OutputSchema(
            enforce_script=False,
            file=Path("/tmp/test_output.txt"),
            prompt_separator="$",
        ),
        backend=BackendSchema(
            endpoint="http://test.endpoint/v1/query",
            auth=AuthSchema(cert_file=Path(""), key_file=Path(""), verify_ssl=True),
        ),
        history=HistorySchema(
            enabled=True, file=Path("/tmp/test_history.json"), max_size=100
        ),
        logging=LoggingSchema(level="debug"),
    )
