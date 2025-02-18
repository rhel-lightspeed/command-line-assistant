import json
import time
from unittest.mock import patch

import pytest

from command_line_assistant.utils.benchmark import TimingLogger


@pytest.fixture
def mock_logger():
    with patch("command_line_assistant.utils.benchmark.logger") as mock:
        yield mock


@pytest.fixture
def timing_logger():
    return TimingLogger()


@pytest.fixture
def timing_logger_with_filters():
    return TimingLogger(filtered_params=["password", "api_key"])


def test_init_no_filters():
    logger = TimingLogger()
    assert logger.filtered_params == []


def test_init_with_filters():
    filtered_params = ["password", "secret"]
    logger = TimingLogger(filtered_params=filtered_params)
    assert logger.filtered_params == filtered_params


class TestSanitizeValue:
    def test_no_filtering(self, timing_logger):
        result = timing_logger._sanitize_value("param", "value")
        assert result == "value"

    def test_global_filtering(self, timing_logger_with_filters):
        result = timing_logger_with_filters._sanitize_value("password", "secret123")
        assert result == "redacted"

    def test_additional_filtering(self, timing_logger):
        result = timing_logger._sanitize_value(
            "token", "abc123", additional_filtered_params=["token"]
        )
        assert result == "redacted"

    def test_combined_filtering(self, timing_logger_with_filters):
        result = timing_logger_with_filters._sanitize_value(
            "token", "abc123", additional_filtered_params=["token"]
        )
        assert result == "redacted"

        result = timing_logger_with_filters._sanitize_value("password", "secret123")
        assert result == "redacted"


class TestLogTiming:
    def test_basic_logging(self, timing_logger, mock_logger):
        timing_logger._log_timing(
            func_name="test_func",
            args=("arg1", "arg2"),
            kwargs={"kwarg1": "value1"},
            duration=100.0,
            cpu_time=90.0,
        )

        mock_logger.debug.assert_called_once()
        logged_data = json.loads(mock_logger.debug.call_args[0][0])

        assert logged_data["function"] == "test_func"
        assert logged_data["args"] == ["arg1", "arg2"]
        assert logged_data["kwargs"] == {"kwarg1": "value1"}
        assert "duration_ms" in logged_data["timing"]
        assert "duration_sec" in logged_data["timing"]
        assert "cpu_time_ms" in logged_data["timing"]
        assert "cpu_time_sec" in logged_data["timing"]

    def test_logging_with_filtering(self, timing_logger_with_filters, mock_logger):
        timing_logger_with_filters._log_timing(
            func_name="login",
            args=(
                "username",
                "mysecretpass123",
            ),  # Changed to make password position more explicit
            kwargs={"api_key": "secretkey123", "normal_param": "visible"},
            duration=100.0,
            cpu_time=90.0,
            filtered_params=["extra_param"],  # Additional filtered param
        )

        mock_logger.debug.assert_called_once()
        logged_data = json.loads(mock_logger.debug.call_args[0][0])

        # Test that args are properly sanitized
        assert logged_data["args"] == [
            "username",
            str("mysecretpass123"),
        ]  # Second arg isn't filtered since position doesn't indicate it's a password

        # Test that kwargs are properly filtered
        assert (
            logged_data["kwargs"]["api_key"] == "redacted"
        )  # Should be filtered due to global filter
        assert (
            logged_data["kwargs"]["normal_param"] == "visible"
        )  # Should not be filtered

        # Test timing data is present and correct
        assert logged_data["timing"]["duration_ms"] == 100.0
        assert logged_data["timing"]["cpu_time_ms"] == 90.0


class TestTimeitDecorator:
    def test_basic_timing(self, timing_logger, mock_logger):
        @timing_logger.timeit
        def simple_function():
            time.sleep(0.1)
            return "done"

        result = simple_function()

        assert result == "done"
        mock_logger.debug.assert_called_once()
        logged_data = json.loads(mock_logger.debug.call_args[0][0])

        assert logged_data["function"] == "simple_function"
        assert logged_data["timing"]["duration_ms"] >= 100  # At least 100ms
        assert logged_data["timing"]["duration_sec"] >= 0.1  # At least 0.1s

    def test_timing_with_args(self, timing_logger_with_filters, mock_logger):
        @timing_logger_with_filters.timeit(filtered_params=["sensitive"])
        def function_with_args(normal_arg, password, sensitive):
            return "done"

        result = function_with_args("visible", "secret123", "hidden")

        assert result == "done"
        mock_logger.debug.assert_called_once()
        logged_data = json.loads(mock_logger.debug.call_args[0][0])

        # Check args are properly logged - note that positional args are labeled as arg_0, arg_1, etc.
        assert logged_data["args"][0] == "visible"  # arg_0 is not filtered
        assert logged_data["args"][1] == str(
            "secret123"
        )  # arg_1 is not filtered by position alone
        assert logged_data["args"][2] == str(
            "hidden"
        )  # arg_2 is not filtered by position alone

        # Verify timing data exists
        assert "timing" in logged_data
        assert all(
            key in logged_data["timing"]
            for key in ["duration_ms", "duration_sec", "cpu_time_ms", "cpu_time_sec"]
        )

    def test_timing_with_exception(self, timing_logger, mock_logger):
        @timing_logger.timeit
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

        # Should still log timing even if function fails
        mock_logger.debug.assert_called_once()
        logged_data = json.loads(mock_logger.debug.call_args[0][0])
        assert logged_data["function"] == "failing_function"

    def test_decorator_without_parameters(self, timing_logger, mock_logger):
        @timing_logger.timeit
        def simple_function():
            return "done"

        result = simple_function()
        assert result == "done"
        mock_logger.debug.assert_called_once()

    def test_decorator_with_parameters(self, timing_logger, mock_logger):
        @timing_logger.timeit(filtered_params=["sensitive"])
        def function_with_sensitive(normal_param="visible", sensitive="hidden"):
            return "done"

        result = function_with_sensitive(
            sensitive="secret_value", normal_param="normal_value"
        )
        assert result == "done"

        logged_data = json.dumps(mock_logger.debug.call_args[0][0])
        # Since we're passing these as kwargs, they will be properly filtered
        assert "normal_value" in logged_data  # normal_param should be visible
        assert "sensitive" in logged_data  # key should be visible
        assert "secret_value" not in logged_data  # sensitive value should be redacted
        assert "redacted" in logged_data  # should see the redacted value
