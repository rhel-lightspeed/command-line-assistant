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


@pytest.fixture(autouse=True)
def setup_logger(request, tmp_path):
    # This makes it so we can skip this using @pytest.mark.noautofixtures
    if "noautofixtures" in request.keywords:
        return

    tmp_log_file = Path(tmp_path / "conftest" / "cla.log")
    logger.setup_logging(
        config.Config(logging=config.LoggingSchema(file=tmp_log_file)), verbose=True
    )

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
            endpoint="http://test.endpoint/v1/query", verify_ssl=True
        ),
        history=HistorySchema(
            enabled=True, file=Path("/tmp/test_history.json"), max_size=100
        ),
        logging=LoggingSchema(type="minimal"),
    )
