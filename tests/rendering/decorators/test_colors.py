import pytest

from command_line_assistant.rendering.decorators.colors import (
    ColorDecorator,
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
