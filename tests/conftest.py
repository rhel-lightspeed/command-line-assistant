import copy
import logging
from argparse import Namespace
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from command_line_assistant import config, logger
from command_line_assistant.config.schemas.backend import AuthSchema, BackendSchema
from command_line_assistant.config.schemas.database import DatabaseSchema
from command_line_assistant.config.schemas.history import HistorySchema
from command_line_assistant.config.schemas.logging import LoggingSchema
from command_line_assistant.dbus import constants as dbus_constants
from command_line_assistant.dbus.context import DaemonContext
from command_line_assistant.logger import LOGGING_CONFIG_DICTIONARY
from command_line_assistant.utils import files
from command_line_assistant.utils.cli import CommandContext
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_text_renderer,
    create_warning_renderer,
)
from tests.helpers import MockStream


@pytest.fixture(autouse=True)
def mock_xdg_path(tmp_path, monkeypatch):
    monkeypatch.setattr(files, "get_xdg_state_path", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def default_kwargs(mock_dbus_service, command_context):
    return {
        "text_renderer": create_text_renderer(),
        "warning_renderer": create_warning_renderer(),
        "error_renderer": create_error_renderer(),
        "args": Namespace(),
        "context": command_context,
        "user_proxy": mock_dbus_service,
        "chat_proxy": mock_dbus_service,
        "history_proxy": mock_dbus_service,
    }


# Mock the entire DBus service/constants module
@pytest.fixture(autouse=True)
def mock_dbus_service(monkeypatch):
    """Fixture to mock DBus service and automatically use it for all tests"""
    internal_mock = mock.MagicMock()
    monkeypatch.setattr(
        dbus_constants.DBusServiceIdentifier, "get_proxy", internal_mock
    )
    return internal_mock.return_value


@pytest.fixture
def command_context():
    return CommandContext(effective_user_id=1000)


@pytest.fixture(autouse=True)
def setup_logger(request):
    # This makes it so we can skip this using @pytest.mark.noautofixtures
    if "noautofixtures" in request.keywords:
        return

    logging_configuration = copy.deepcopy(LOGGING_CONFIG_DICTIONARY)
    with patch(
        "command_line_assistant.logger.LOGGING_CONFIG_DICTIONARY", logging_configuration
    ):
        logger._setup_logging(logging_level="DEBUG", handlers=[])

        # get root logger
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)


class MockPwnam:
    def __init__(self, pw_uid="1000"):
        self._pw_uid = pw_uid

    @property
    def pw_uid(self):
        return self._pw_uid


@pytest.fixture
def mock_config(tmp_path):
    """Fixture to create a mock configuration"""
    cert_file = tmp_path / "cert.pem"
    key_file = tmp_path / "key.pem"
    history_db = tmp_path / "history.db"

    cert_file.write_text("cert")
    key_file.write_text("key")
    with patch("pwd.getpwnam", return_value=MockPwnam()):
        return config.Config(
            backend=BackendSchema(
                endpoint="http://localhost",
                auth=AuthSchema(
                    cert_file=cert_file, key_file=key_file, verify_ssl=False
                ),
            ),
            history=HistorySchema(
                enabled=True,
            ),
            database=DatabaseSchema(type="sqlite", connection_string=history_db),
            logging=LoggingSchema(
                level="debug",
            ),
        )


@pytest.fixture
def mock_dbus_session():
    """Create a mock DBus session."""
    return MagicMock()


@pytest.fixture
def mock_stream():
    return MockStream()


@pytest.fixture
def mock_context(mock_config):
    return DaemonContext(mock_config)


@pytest.fixture
def universal_user_id():
    return "ca427c50-ff49-11ef-9209-52b437312584"
