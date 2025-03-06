import os
import shutil
from typing import Iterator
from unittest import mock

import pytest

from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
    TextWrapDecorator,
    WriteOncePerSessionDecorator,
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


class TestWriteOncePerSessionDecorator:
    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Fixture to provide a temporary state directory"""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        return state_dir

    @pytest.fixture
    def decorator(self, temp_state_dir, monkeypatch):
        """Fixture to provide a WriteOnceDecorator with mocked state directory"""
        monkeypatch.setattr(
            "command_line_assistant.rendering.decorators.text.get_xdg_state_path",
            lambda: temp_state_dir,
        )
        return WriteOncePerSessionDecorator("test_state")

    def test_first_write(self, decorator):
        """Test first write with decorator"""
        text = "First time text"
        result = decorator.decorate(text)
        assert result == text
        assert decorator._state_file.exists()

    def test_subsequent_write(self, decorator):
        """Test subsequent writes with decorator"""
        first_result = decorator.decorate("First write")
        second_result = decorator.decorate("Second write")
        assert first_result == "First write"
        assert not second_result

    def test_different_state_files(self, temp_state_dir, monkeypatch):
        """Test different state files for different instances"""
        monkeypatch.setattr(
            "command_line_assistant.rendering.decorators.text.get_xdg_state_path",
            lambda: temp_state_dir,
        )

        decorator1 = WriteOncePerSessionDecorator("state1")
        decorator2 = WriteOncePerSessionDecorator("state2")

        result1 = decorator1.decorate("Text 1")
        result2 = decorator2.decorate("Text 2")

        assert result1 == "Text 1"
        assert result2 == "Text 2"
        assert decorator1._state_file != decorator2._state_file

    def test_state_directory_creation(self, temp_state_dir, monkeypatch):
        """Test state directory creation if it doesn't exist"""
        non_existent_dir = temp_state_dir / "subdir"
        monkeypatch.setattr(
            "command_line_assistant.rendering.decorators.text.get_xdg_state_path",
            lambda: non_existent_dir,
        )

        decorator = WriteOncePerSessionDecorator("test_state")
        decorator.decorate("Test text")

        assert non_existent_dir.exists()
        assert decorator._state_file.exists()

    def test_empty_text(self, decorator):
        """Test decorator with empty text"""
        result = decorator.decorate("")
        assert result == ""
        assert decorator._state_file.exists()

    def test_multiple_decorators_same_file(self, temp_state_dir, monkeypatch):
        """Test multiple decorators using the same state file"""
        monkeypatch.setattr(
            "command_line_assistant.rendering.decorators.text.get_xdg_state_path",
            lambda: temp_state_dir,
        )

        decorator1 = WriteOncePerSessionDecorator("same_state")
        decorator2 = WriteOncePerSessionDecorator("same_state")

        result1 = decorator1.decorate("First text")
        result2 = decorator2.decorate("Second text")

        assert result1 == "First text"
        assert not result2

    def test_state_file_permissions(self, decorator):
        """Test state file permissions"""
        decorator.decorate("Test text")
        assert decorator._state_file.exists()
        assert oct(decorator._state_file.stat().st_mode)[-3:] == "600"

    @pytest.mark.parametrize(
        "filename",
        [
            "test-state",
            "test_state",
            "test.state",
            "TEST_STATE",
            "123_state",
            "state_123",
        ],
    )
    def test_various_filenames(self, temp_state_dir, monkeypatch, filename):
        """Test decorator with various valid state filenames"""
        monkeypatch.setattr(
            "command_line_assistant.rendering.decorators.text.get_xdg_state_path",
            lambda: temp_state_dir,
        )

        decorator = WriteOncePerSessionDecorator(filename)
        result = decorator.decorate("Test text")

        assert result == "Test text"
        assert decorator._state_file.exists()

    def test_different_pid(self, temp_state_dir, monkeypatch):
        monkeypatch.setattr(
            "command_line_assistant.rendering.decorators.text.get_xdg_state_path",
            lambda: temp_state_dir,
        )
        monkeypatch.setattr("os.getppid", mock.Mock(side_effect=[0, 0, 1]))

        decorator = WriteOncePerSessionDecorator("test")
        assert decorator.decorate("Test text") == "Test text"

        decorator = WriteOncePerSessionDecorator("test")
        assert not decorator.decorate("Test second")

        decorator = WriteOncePerSessionDecorator("test")
        assert decorator.decorate("Test third") == "Test third"

        assert decorator._state_file.exists()


def test_write_once_decorator_creates_state_file(tmp_path, monkeypatch):
    """Test that WriteOncePerSessionDecorator creates a state file"""
    monkeypatch.setattr(
        "command_line_assistant.rendering.decorators.text.get_xdg_state_path",
        lambda: tmp_path,
    )

    state_file = tmp_path / "test_state"
    decorator = WriteOncePerSessionDecorator("test_state")
    assert not state_file.exists()

    decorator.decorate("Test text")
    assert state_file.exists()
    assert state_file.read_text() == str(os.getppid())
