from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
    TextWrapDecorator,
)


def test_text_wrap_decorator():
    decorator = TextWrapDecorator(width=10)
    text = "This is a long text that should be wrapped"
    decorated = decorator.decorate(text)
    assert len(max(decorated.split("\n"), key=len)) <= 10


def test_emoji_decorator():
    decorator = EmojiDecorator("⭐")
    text = "Test text"
    assert decorator.decorate(text) == "⭐ Test text"


def test_emoji_decorator_with_hex():
    decorator = EmojiDecorator(0x2728)  # Sparkles emoji
    text = "Test text"
    assert decorator.decorate(text) == "✨ Test text"


def test_emoji_decorator_with_unicode():
    decorator = EmojiDecorator("U+1F4A5")  # Collision emoji
    text = "Test text"
    assert decorator.decorate(text) == "💥 Test text"
