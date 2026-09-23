import pytest

from command_line_assistant.rendering import renderers
from command_line_assistant.rendering.colors import Color, Style
from command_line_assistant.rendering.renderers import Renderer
from command_line_assistant.rendering.theme import Theme


class TestDeprecationRenderer:
    """Test cases for the Renderer.deprecation() method."""

    def test_deprecation_plain_mode(self, capsys, disable_stream_flush):
        """Test deprecation message in plain mode outputs prefix + message without ANSI codes."""
        renderer = Renderer(plain=True)
        renderer.deprecation("test message")

        captured = capsys.readouterr()
        assert "Deprecated: test message" in captured.out
        # Plain mode should not contain ANSI escape codes
        assert "\033[" not in captured.out

    def test_deprecation_custom_prefix(self, capsys, disable_stream_flush):
        """Test deprecation message with a custom prefix."""
        renderer = Renderer(plain=True)
        renderer.deprecation("test message", prefix="Warning: ")

        captured = capsys.readouterr()
        assert "Warning: test message" in captured.out
        assert "Deprecated: " not in captured.out

    def test_deprecation_colored_mode(self, capsys, disable_stream_flush):
        """Test deprecation message in colored mode outputs bold red prefix and red body."""
        renderer = Renderer(plain=False, theme=Theme())
        renderer.deprecation("test message")

        captured = capsys.readouterr()
        # Should contain the text
        assert "Deprecated: " in captured.out
        assert "test message" in captured.out
        # Should contain RED ANSI code (error color)
        assert Color.RED.value in captured.out
        # Should contain BOLD ANSI code for the prefix
        assert Style.BOLD.value in captured.out


@pytest.mark.parametrize(
    ("size", "expected"),
    (
        # Test bytes (< 1000)
        (0, "0.00 B"),
        (1, "1.00 B"),
        (42, "42.00 B"),
        (248, "248.00 B"),
        (567, "567.00 B"),
        (999, "999.00 B"),
        # Test KB boundary and values
        (1000, "1.00 KB"),
        (999999, "1000.00 KB"),
        # Test MB boundary and values
        (1000000, "1.00 MB"),
        (999999999, "1000.00 MB"),
        # Test GB boundary and values
        (1000000000, "1.00 GB"),
        (999999999999, "1000.00 GB"),
        # Test TB boundary and values
        (1000000000000, "1.00 TB"),
        # Test PB boundary and values
        (1000000000000000, "1.00 PB"),
        # Test float inputs
        (1500.5, "1.50 KB"),
        (2500.75, "2.50 KB"),
        (32000, "32.00 KB"),
        (1234567.89, "1.23 MB"),
        (9876543210.123, "9.88 GB"),
        # Test edge cases and random values
        (1234567, "1.23 MB"),
        (9876543, "9.88 MB"),
        (123456789, "123.46 MB"),
        (987654321, "987.65 MB"),
        (1234567890, "1.23 GB"),
        (9876543210, "9.88 GB"),
    ),
)
def test_human_readable_size(size, expected):
    assert renderers.human_readable_size(size) == expected
