"""
Unit tests for the colorize and stylize functions in colors.py.
"""

import os
from unittest.mock import patch

import pytest

from command_line_assistant.rendering.colors import Color, Style, colorize, stylize


class TestColorizeFunction:
    """Test cases for the colorize function."""

    def test_colorize_with_color_enum(self):
        """Test colorize function with Color enum values."""
        text = "Hello, World!"
        result = colorize(text, Color.RED)

        expected = f"{Color.RED.value}{text}{Color.NORMAL.value}"
        assert result == expected
        assert result.startswith("\033[31m")  # Red ANSI code
        assert result.endswith("\033[0m")  # Normal/reset ANSI code
        assert text in result

    def test_colorize_with_string_color(self):
        """Test colorize function with string color names."""
        text = "Hello, World!"
        result = colorize(text, "blue")

        expected = f"{Color.BLUE.value}{text}{Color.NORMAL.value}"
        assert result == expected
        assert result.startswith("\033[34m")  # Blue ANSI code
        assert result.endswith("\033[0m")  # Normal/reset ANSI code

    def test_colorize_with_string_color_case_insensitive(self):
        """Test colorize function with different case string colors."""
        text = "Test"

        # Test lowercase
        result_lower = colorize(text, "green")
        # Test uppercase
        result_upper = colorize(text, "GREEN")
        # Test mixed case
        result_mixed = colorize(text, "Green")

        expected = f"{Color.GREEN.value}{text}{Color.NORMAL.value}"
        assert result_lower == expected
        assert result_upper == expected
        assert result_mixed == expected

    def test_colorize_all_colors(self):
        """Test colorize function with all available colors."""
        text = "Test"

        for color in Color:
            if color != Color.NORMAL:  # Skip NORMAL as it's used for reset
                result = colorize(text, color)
                assert result.startswith(color.value)
                assert result.endswith(Color.NORMAL.value)
                assert text in result

    def test_colorize_bright_colors(self):
        """Test colorize function with bright color variants."""
        text = "Bright text"

        bright_colors = [
            Color.BRIGHT_BLACK,
            Color.BRIGHT_RED,
            Color.BRIGHT_GREEN,
            Color.BRIGHT_YELLOW,
            Color.BRIGHT_BLUE,
            Color.BRIGHT_MAGENTA,
            Color.BRIGHT_CYAN,
            Color.BRIGHT_WHITE,
        ]

        for color in bright_colors:
            result = colorize(text, color)
            assert result.startswith(color.value)
            assert result.endswith(Color.NORMAL.value)
            assert text in result

    def test_colorize_with_no_color_env_var(self):
        """Test colorize function respects NO_COLOR environment variable."""
        text = "No color text"

        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=True):
            result = colorize(text, Color.RED)
            assert result == text  # Should return original text without ANSI codes

            result_string = colorize(text, "blue")
            assert result_string == text

    def test_colorize_with_no_color_various_values(self):
        """Test colorize function with various NO_COLOR values."""
        text = "Test text"

        # Test various truthy values for NO_COLOR
        truthy_values = ["1", "true", "TRUE", "yes", "anything"]

        for value in truthy_values:
            with patch.dict(os.environ, {"NO_COLOR": value}, clear=True):
                result = colorize(text, Color.GREEN)
                assert result == text, f"Failed for NO_COLOR={value}"

    def test_colorize_empty_string(self):
        """Test colorize function with empty string."""
        result = colorize("", Color.RED)
        expected = f"{Color.RED.value}{Color.NORMAL.value}"
        assert result == expected

    def test_colorize_multiline_string(self):
        """Test colorize function with multiline strings."""
        text = "Line 1\nLine 2\nLine 3"
        result = colorize(text, Color.YELLOW)

        expected = f"{Color.YELLOW.value}{text}{Color.NORMAL.value}"
        assert result == expected
        assert "\n" in result  # Newlines should be preserved

    def test_colorize_with_special_characters(self):
        """Test colorize function with special characters."""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = colorize(special_chars, Color.CYAN)

        expected = f"{Color.CYAN.value}{special_chars}{Color.NORMAL.value}"
        assert result == expected

    def test_colorize_invalid_string_color(self):
        """Test colorize function with invalid string color raises KeyError."""
        text = "Test"

        with pytest.raises(KeyError):
            colorize(text, "invalid_color")

        with pytest.raises(KeyError):
            colorize(text, "purple")  # Not in our Color enum


class TestStylizeFunction:
    """Test cases for the stylize function."""

    def test_stylize_with_style_enum(self):
        """Test stylize function with Style enum values."""
        text = "Styled text"
        result = stylize(text, Style.BOLD)

        expected = f"{Style.BOLD.value}{text}{Style.NORMAL.value}"
        assert result == expected
        assert result.startswith("\033[1m")  # Bold ANSI code
        assert result.endswith("\033[0m")  # Normal/reset ANSI code
        assert text in result

    def test_stylize_all_styles(self):
        """Test stylize function with all available styles."""
        text = "Test"

        for style in Style:
            if style != Style.NORMAL:  # Skip NORMAL as it's used for reset
                result = stylize(text, style)
                assert result.startswith(style.value)
                assert result.endswith(Style.NORMAL.value)
                assert text in result

    def test_stylize_individual_styles(self):
        """Test stylize function with each individual style."""
        text = "Style test"

        # Test Bold
        result = stylize(text, Style.BOLD)
        assert result.startswith("\033[1m")

        # Test Italic
        result = stylize(text, Style.ITALIC)
        assert result.startswith("\033[3m")

        # Test Underline
        result = stylize(text, Style.UNDERLINE)
        assert result.startswith("\033[4m")

        # Test Strikethrough
        result = stylize(text, Style.STRIKETHROUGH)
        assert result.startswith("\033[9m")

    def test_stylize_with_no_color_env_var(self):
        """Test stylize function respects NO_COLOR environment variable."""
        text = "No style text"

        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=True):
            result = stylize(text, Style.BOLD)
            assert result == text  # Should return original text without ANSI codes

            result = stylize(text, Style.ITALIC)
            assert result == text

    def test_stylize_with_no_color_various_values(self):
        """Test stylize function with various NO_COLOR values."""
        text = "Test text"

        # Test various truthy values for NO_COLOR
        truthy_values = ["1", "true", "TRUE", "yes", "anything"]

        for value in truthy_values:
            with patch.dict(os.environ, {"NO_COLOR": value}, clear=True):
                result = stylize(text, Style.UNDERLINE)
                assert result == text, f"Failed for NO_COLOR={value}"

    def test_stylize_empty_string(self):
        """Test stylize function with empty string."""
        result = stylize("", Style.BOLD)
        expected = f"{Style.BOLD.value}{Style.NORMAL.value}"
        assert result == expected

    def test_stylize_multiline_string(self):
        """Test stylize function with multiline strings."""
        text = "Line 1\nLine 2\nLine 3"
        result = stylize(text, Style.ITALIC)

        expected = f"{Style.ITALIC.value}{text}{Style.NORMAL.value}"
        assert result == expected
        assert "\n" in result  # Newlines should be preserved

    def test_stylize_with_special_characters(self):
        """Test stylize function with special characters."""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = stylize(special_chars, Style.UNDERLINE)

        expected = f"{Style.UNDERLINE.value}{special_chars}{Style.NORMAL.value}"
        assert result == expected


class TestColorAndStyleEnums:
    """Test cases for Color and Style enum functionality."""

    def test_color_enum_str_method(self):
        """Test Color enum __str__ method returns ANSI value."""
        assert str(Color.RED) == "\033[31m"
        assert str(Color.BLUE) == "\033[34m"
        assert str(Color.NORMAL) == "\033[0m"

    def test_style_enum_str_method(self):
        """Test Style enum __str__ method returns ANSI value."""
        assert str(Style.BOLD) == "\033[1m"
        assert str(Style.ITALIC) == "\033[3m"
        assert str(Style.NORMAL) == "\033[0m"


class TestIntegrationScenarios:
    """Integration test scenarios combining colorize and stylize."""

    def test_colorize_then_stylize_no_conflict(self):
        """Test that colorize and stylize can be used independently."""
        text = "Test text"

        # These should work independently
        colored = colorize(text, Color.RED)
        styled = stylize(text, Style.BOLD)

        assert colored != styled
        assert Color.RED.value in colored
        assert Style.BOLD.value in styled

    def test_unicode_text_support(self):
        """Test colorize and stylize with unicode text."""
        unicode_text = "Hello 世界 🌍 émojis"

        colored = colorize(unicode_text, Color.GREEN)
        styled = stylize(unicode_text, Style.BOLD)

        assert unicode_text in colored
        assert unicode_text in styled
        assert colored.startswith(Color.GREEN.value)
        assert styled.startswith(Style.BOLD.value)

    def test_very_long_text(self):
        """Test colorize and stylize with very long text."""
        long_text = "A" * 10000  # 10k characters

        colored = colorize(long_text, Color.BLUE)
        styled = stylize(long_text, Style.ITALIC)

        assert long_text in colored
        assert long_text in styled
        assert len(colored) > len(long_text)  # Should be longer due to ANSI codes
        assert len(styled) > len(long_text)

    def test_no_color_affects_both_functions(self):
        """Test that NO_COLOR environment variable affects both functions."""
        text = "Test text"

        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=True):
            colored = colorize(text, Color.RED)
            styled = stylize(text, Style.BOLD)

            assert colored == text
            assert styled == text
