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


@patch("builtins.input", side_effect=KeyboardInterrupt)
def test_interactive_renderer_keyboard_interrupt(mock_input, interactive_renderer):
    """Test that KeyboardInterrupt raises StopInteractiveMode"""
    with pytest.raises(
        StopInteractiveMode,
        match="Detected keyboard interrupt. Stopping interactive mode.",
    ):
        interactive_renderer.render(">>> ")


@patch("builtins.input", side_effect=EOFError)
def test_interactive_renderer_eof_error(mock_input, interactive_renderer):
    """Test that EOFError raises StopInteractiveMode"""
    with pytest.raises(
        StopInteractiveMode,
        match="Detected keyboard interrupt. Stopping interactive mode.",
    ):
        interactive_renderer.render(">>> ")
