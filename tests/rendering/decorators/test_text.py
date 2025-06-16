import shutil
from typing import Iterator

import pytest

from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
    TextWrapDecorator,
)


class TestEmojiDecorator:
    @pytest.mark.parametrize(
        ("emoji_input", "expected"),
        [
            ("👍", "👍 Test text"),  # Direct emoji
            ("🚀", "🚀 Test text"),  # Direct emoji
            ("⭐", "⭐ Test text"),  # Direct emoji
            (0x1F604, "😄 Test text"),  # Unicode code point as int
            ("U+1F604", "😄 Test text"),  # Unicode code point as string
            ("0x1F604", "😄 Test text"),  # Hex code point as string
        ],
    )
    def test_emoji_decorator(self, emoji_input, expected):
        """Test emoji decorator with various input formats"""
        decorator = EmojiDecorator(emoji_input)
        result = decorator.decorate("Test text")
        assert result == expected

    def test_invalid_emoji_type(self):
        """Test emoji decorator with invalid input type"""
        with pytest.raises(TypeError, match="Emoji must be string or int"):
            EmojiDecorator([1, 2, 3])  # type: ignore

    @pytest.mark.parametrize(
        "emoji_code",
        [
            0x1F600,  # Grinning face
            0x2B50,  # Star
            0x1F680,  # Rocket
            0x1F44D,  # Thumbs up
            0x2764,  # Heart
        ],
    )
    def test_numeric_emoji_codes(self, emoji_code):
        """Test emoji decorator with different numeric Unicode code points"""
        decorator = EmojiDecorator(emoji_code)
        result = decorator.decorate("Test")
        assert len(result.split()[0]) <= 2  # Emoji should be 1-2 characters
        assert result.endswith("Test")

    def test_emoji_with_empty_text(self):
        """Test emoji decorator with empty text"""
        decorator = EmojiDecorator("🎉")
        result = decorator.decorate("")
        assert result == "🎉 "

    def test_emoji_with_multiline_text(self):
        """Test emoji decorator with multiline text"""
        decorator = EmojiDecorator("📝")
        text = "Line 1\nLine 2\nLine 3"
        result = decorator.decorate(text)
        assert result == "📝 " + text


class TestTextWrapDecorator:
    @pytest.fixture
    def terminal_width(self) -> Iterator[int]:
        """Fixture to get the terminal width"""
        original_terminal_size = shutil.get_terminal_size()
        yield original_terminal_size.columns

    def test_default_width(self, terminal_width):
        """Test text wrap decorator with default width"""
        decorator = TextWrapDecorator()
        assert decorator._width == terminal_width

    def test_custom_width(self):
        """Test text wrap decorator with custom width"""
        decorator = TextWrapDecorator(width=40)
        assert decorator._width == 40

    def test_custom_indent(self):
        """Test text wrap decorator with custom indent"""
        decorator = TextWrapDecorator(indent="  ")
        assert decorator._indent == "  "

    @pytest.mark.parametrize(
        ("width", "indent", "text", "expected"),
        [
            (20, "", "Short text", "Short text"),
            (
                10,
                "",
                "This is a long text that should wrap",
                "This is a\nlong text\nthat\nshould\nwrap",
            ),
            (10, "  ", "Indented text wrap test", "  Indented\n  text\n  wrap\n  test"),
            (
                15,
                "-> ",
                "Multiple line indent test",
                "-> Multiple\n-> line indent\n-> test",
            ),
        ],
    )
    def test_text_wrapping(self, width, indent, text, expected):
        """Test text wrapping with various configurations"""
        decorator = TextWrapDecorator(width=width, indent=indent)
        result = decorator.decorate(text)
        assert result == expected

    def test_long_word_handling(self):
        """Test handling of words longer than wrap width"""
        decorator = TextWrapDecorator(width=10)
        result = decorator.decorate("supercalifragilisticexpialidocious")
        assert max(len(line) for line in result.split("\n")) >= 10

    def test_empty_text(self):
        """Test wrapping empty text"""
        decorator = TextWrapDecorator(width=10)
        result = decorator.decorate("")
        assert result == ""

    def test_whitespace_handling(self):
        """Test handling of various whitespace scenarios"""
        decorator = TextWrapDecorator(width=10)
        text = "   Multiple    spaces    test   "
        result = decorator.decorate(text)
        assert "    " not in result  # Should not contain multiple consecutive spaces
