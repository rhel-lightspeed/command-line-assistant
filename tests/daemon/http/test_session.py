from unittest.mock import MagicMock, patch

import pytest
import urllib3

from command_line_assistant.constants import VERSION
from command_line_assistant.daemon.http.session import get_session
from command_line_assistant.dbus.exceptions import RequestFailedError


def test_session_headers(mock_config):
    """Test that session headers are properly set"""
    session = get_session(mock_config)

    assert session.headers["User-Agent"] == f"clad/{VERSION}"
    assert session.headers["Content-Type"] == "application/json"


def test_ssl_verification_disabledmock_config(mock_config):
    """Test that SSL verification is disabled when configured"""

    with patch("urllib3.disable_warnings") as mock_disable_warnings:
        session = get_session(mock_config)

        mock_disable_warnings.assert_called_once_with(
            urllib3.exceptions.InsecureRequestWarning
        )
        assert session.verify is False


@patch("command_line_assistant.daemon.http.session.Session")
def test_session_creation(mock_session, mock_config):
    """Test basic session creation"""
    mock_session_instance = MagicMock()
    mock_session.return_value = mock_session_instance

    session = get_session(mock_config)

    mock_session.assert_called_once()
    assert session == mock_session_instance


def test_ssl_verification_disabled_logs_warning(caplog, mock_config):
    """Test that disabling SSL verification logs a warning"""
    with patch("urllib3.disable_warnings"):
        get_session(mock_config)

    assert "Disabling SSL verification as per user requested." in caplog.text


def test_different_endpoint_configuration(mock_config):
    """Test session creation with different endpoint configurations"""
    custom_endpoint = "https://custom-endpoint:9090"
    mock_config.backend.endpoint = custom_endpoint

    session = get_session(mock_config)

    # Verify that the custom endpoint is used for mounting adapters
    assert any(pattern == custom_endpoint for pattern, _ in session.adapters.items())


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://localhost:8080",
        "https://api.example.com",
        "http://127.0.0.1:5000",
    ],
)
def test_various_endpoints(mock_config, endpoint):
    """Test session creation with various endpoint configurations"""
    mock_config.backend.endpoint = endpoint
    session = get_session(mock_config)

    # Verify that the endpoint is used for mounting adapters
    assert any(pattern == endpoint for pattern, _ in session.adapters.items())


def test_session_with_corrupted_ssl_certificate(mock_config):
    mock_config.backend.auth.cert_file.write_text("whatever pem")
    mock_config.backend.auth.key_file.write_text("whatever secret")
    mock_config.backend.auth.verify_ssl = True

    with pytest.raises(
        RequestFailedError, match="Failed to load certificate in cert chain."
    ):
        get_session(mock_config)


def test_session_with_missing_ssl_certificate(tmp_path, mock_config):
    cert_file = tmp_path / "missing" / "cert.pem"
    key_file = tmp_path / "missing" / "key.pem"

    mock_config.backend.auth.cert_file = cert_file
    mock_config.backend.auth.key_file = key_file
    mock_config.backend.auth.verify_ssl = True

    with pytest.raises(RequestFailedError, match="Couldn't find certificate files at"):
        get_session(mock_config)
