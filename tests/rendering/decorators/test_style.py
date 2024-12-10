import pytest

from command_line_assistant.rendering.decorators.style import StyleDecorator


def test_style_decorator_single_style():
    decorator = StyleDecorator("bright")
    text = "Test text"
    styled_text = decorator.decorate(text)
    assert styled_text != text  # Style was applied
    assert len(styled_text) > len(text)  # Reset code was added


def test_style_decorator_invalid_style():
    with pytest.raises(ValueError):
        StyleDecorator("invalid_style")


def test_style_decorator_empty():
    decorator = StyleDecorator()
    text = "Test text"
    styled_text = decorator.decorate(text)
    assert styled_text.endswith(text)  # Text is at the end after any styles


def test_style_decorator_reset():
    decorator = StyleDecorator("bright")
    text = "Test text"
    styled_text = decorator.decorate(text)
    assert "\x1b[1mTest text\x1b[0m" == styled_text
