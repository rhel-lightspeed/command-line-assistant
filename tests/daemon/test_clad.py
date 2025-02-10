from unittest.mock import Mock, patch

import pytest

from command_line_assistant.config import Config
from command_line_assistant.daemon.clad import daemonize


@pytest.fixture
def mock_config():
    return Mock(spec=Config)


@pytest.fixture
def mock_setup_logging():
    with patch("command_line_assistant.daemon.clad.setup_daemon_logging") as mock:
        yield mock


@pytest.fixture
def mock_serve():
    with patch("command_line_assistant.daemon.clad.serve") as mock:
        yield mock


@pytest.fixture
def mock_load_config():
    with patch("command_line_assistant.daemon.clad.load_config_file") as mock:
        mock.return_value = Mock(spec=Config)
        yield mock


class TestClad:
    def test_daemonize_successful(
        self, mock_config, mock_setup_logging, mock_serve, mock_load_config
    ):
        """Test successful daemon initialization"""
        # Act
        result = daemonize()

        # Assert
        mock_load_config.assert_called_once()
        mock_setup_logging.assert_called_once()
        mock_serve.assert_called_once()
        assert result == 0

    def test_daemonize_load_config_error(
        self, mock_load_config, mock_setup_logging, mock_serve
    ):
        """Test daemon initialization when config loading fails"""
        # Arrange
        mock_load_config.side_effect = Exception("Config load error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            daemonize()

        assert str(exc_info.value) == "Config load error"
        mock_setup_logging.assert_not_called()
        mock_serve.assert_not_called()

    def test_daemonize_setup_logging_error(
        self, mock_load_config, mock_setup_logging, mock_serve
    ):
        """Test daemon initialization when logging setup fails"""
        # Arrange
        mock_setup_logging.side_effect = Exception("Logging setup error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            daemonize()

        assert str(exc_info.value) == "Logging setup error"
        mock_load_config.assert_called_once()
        mock_serve.assert_not_called()

    def test_daemonize_serve_error(
        self, mock_load_config, mock_setup_logging, mock_serve
    ):
        """Test daemon initialization when serve fails"""
        # Arrange
        mock_serve.side_effect = Exception("Serve error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            daemonize()

        assert str(exc_info.value) == "Serve error"
        mock_load_config.assert_called_once()
        mock_setup_logging.assert_called_once()
