import logging

import pytest

from command_line_assistant import config, logger


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
