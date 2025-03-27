from unittest.mock import patch

import pytest

from command_line_assistant.exceptions import StopInteractiveMode
from command_line_assistant.rendering.renders.interactive import InteractiveRenderer
from command_line_assistant.rendering.stream import StdoutStream


@pytest.fixture
def interactive_renderer():
    """Fixture to create an InteractiveRenderer instance"""
    banner = "Welcome to test interactive mode!"
    return InteractiveRenderer(banner=banner)


def test_interactive_renderer_init(interactive_renderer):
    """Test the initialization of InteractiveRenderer"""
    assert isinstance(interactive_renderer._stream, StdoutStream)
    assert interactive_renderer._banner == "Welcome to test interactive mode!"
    assert interactive_renderer._output == ""
    assert interactive_renderer._first_message is False


@patch("builtins.input", return_value="test input")
def test_interactive_renderer_input(mock_input, interactive_renderer):
    """Test that user input is captured correctly"""
    interactive_renderer.render(">>> ")
    assert interactive_renderer.output == "test input"
    mock_input.assert_called_once_with(">>> ")


@patch("builtins.input", return_value=".exit")
def test_interactive_renderer_exit_command(mock_input, interactive_renderer):
    """Test that .exit command raises StopInteractiveMode"""
    with pytest.raises(StopInteractiveMode, match="Stopping interactive mode."):
        interactive_renderer.render(">>> ")


def test_interactive_renderer_banner_display(capsys):
    """Test that interactive renderer displays banner on first render"""
    banner = "Welcome to test interactive mode!"
    renderer = InteractiveRenderer(banner=banner)

    with patch("builtins.input", return_value="test"):
        renderer.render(">>> ")

    captured = capsys.readouterr()
    assert banner in captured.out
    assert "The current session does not include running context" in captured.out

    # Second render should not show banner again
    with patch("builtins.input", return_value="test"):
        renderer.render(">>> ")

    captured = capsys.readouterr()
    assert banner not in captured.out
