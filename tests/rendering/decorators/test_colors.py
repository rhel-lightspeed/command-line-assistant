import os
from unittest.mock import patch

import pytest

from command_line_assistant.rendering.decorators.colors import (
    ColorDecorator,
    should_disable_color_output,
)


def test_color_decorator_basic():
    decorator = ColorDecorator(foreground="red")
    text = "Test text"
    result = decorator.decorate(text)
    assert result.startswith("\x1b[31m")  # Red color code
    assert result.endswith("\x1b[0m")  # Reset code
    assert "Test text" in result


def test_color_decorator_with_background():
    decorator = ColorDecorator(foreground="white", background="blue")
    text = "Test text"
    result = decorator.decorate(text)
    assert result.startswith("\x1b[44m")  # Blue background code
    assert "\x1b[37m" in result  # White foreground code
    assert result.endswith("\x1b[0m")
    assert "Test text" in result


def test_color_decorator_invalid_color():
    with pytest.raises(ValueError):
        ColorDecorator(foreground="invalid")

    with pytest.raises(ValueError):
        ColorDecorator(foreground="white", background="invalid")


@pytest.mark.parametrize(
    ("env_value", "expected"),
    [
        ("1", True),
        ("true", True),
        ("TRUE", True),
        ("True", True),
        ("yes", True),
        ("YES", True),
        ("anything", True),  # Any non-empty value except "0" or "false"
        ("0", False),
        ("false", False),
        ("FALSE", False),
        ("False", False),
        (None, False),  # NO_COLOR not set
    ],
)
def test_should_disable_color_output(env_value, expected):
    """Test different NO_COLOR environment variable values"""
    with patch.dict(
        os.environ, {"NO_COLOR": env_value} if env_value is not None else {}, clear=True
    ):
        assert should_disable_color_output() == expected


def test_should_disable_color_output_no_env():
    """Test when NO_COLOR environment variable is not set"""
    with patch.dict(os.environ, {}, clear=True):
        assert should_disable_color_output() is False


def test_should_disable_color_output_empty_string():
    """Test when NO_COLOR is set to empty string"""
    with patch.dict(os.environ, {"NO_COLOR": ""}, clear=True):
        assert should_disable_color_output() is True


@pytest.mark.parametrize(
    ("env_vars", "expected"),
    [
        ({"NO_COLOR": "1", "TERM": "xterm"}, True),  # NO_COLOR takes precedence
        ({"NO_COLOR": "0", "TERM": "dumb"}, False),  # NO_COLOR takes precedence
        ({"TERM": "dumb"}, False),  # Only TERM present
        ({}, False),  # No environment variables set
    ],
)
def test_should_disable_color_output_with_other_env(env_vars, expected):
    """Test interaction with other environment variables"""
    with patch.dict(os.environ, env_vars, clear=True):
        assert should_disable_color_output() == expected
