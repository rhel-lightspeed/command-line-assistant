from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from command_line_assistant.commands.shell import (
    BaseShellOperation,
    DisableInteractiveMode,
    DisablePersistentCapture,
    EnableInteractiveMode,
    EnablePersistentCapture,
    EnableTerminalCapture,
    ShellCommand,
    ShellOperationFactory,
)
from command_line_assistant.rendering.renders.text import TextRenderer


@pytest.fixture
def mock_text_renderer():
    renderer = MagicMock(spec=TextRenderer)
    return renderer


@pytest.fixture
def shell_operation_factory(mock_text_renderer):
    return ShellOperationFactory(mock_text_renderer, mock_text_renderer)


@pytest.fixture
def base_shell_operation(mock_text_renderer):
    return BaseShellOperation(mock_text_renderer, mock_text_renderer)


# Test Shell Operation Factory
def test_shell_operation_factory_registration():
    """Test operation registration in factory"""
    factory = ShellOperationFactory(MagicMock(), MagicMock())

    # Verify all operations are registered
    assert EnableInteractiveMode in factory._operations.values()
    assert DisableInteractiveMode in factory._operations.values()
    assert EnablePersistentCapture in factory._operations.values()
    assert DisablePersistentCapture in factory._operations.values()
    assert EnableTerminalCapture in factory._operations.values()


def test_shell_operation_factory_create_operation(shell_operation_factory):
    """Test creation of operations through factory"""
    # Test enable interactive mode
    args = Namespace(
        enable_interactive=True,
        disable_interactive=False,
        enable_persistent_capture=False,
        disable_persistent_capture=False,
        enable_capture=False,
    )
    operation = shell_operation_factory.create_operation(args)
    assert isinstance(operation, EnableInteractiveMode)

    # Test disable interactive mode
    args = Namespace(
        enable_interactive=False,
        disable_interactive=True,
        enable_persistent_capture=False,
        disable_persistent_capture=False,
        enable_capture=False,
    )
    operation = shell_operation_factory.create_operation(args)
    assert isinstance(operation, DisableInteractiveMode)


def test_shell_operation_factory_no_operation(shell_operation_factory):
    """Test factory returns None when no operation specified"""
    args = Namespace(
        enable_interactive=False,
        disable_interactive=False,
        enable_persistent_capture=False,
        disable_persistent_capture=False,
        enable_capture=False,
    )
    operation = shell_operation_factory.create_operation(args)
    assert operation is None


# Test Base Shell Operation
@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.write_text")
def test_base_shell_operation_initialize_bash_folder(
    mock_write, mock_mkdir, base_shell_operation
):
    """Test initialization of bash folder"""
    base_shell_operation._initialize_bash_folder()
    mock_mkdir.assert_called_once()
    mock_write.assert_called_once()


@patch("pathlib.Path.exists")
@patch("pathlib.Path.write_text")
def test_base_shell_operation_write_bash_functions(
    mock_write, mock_exists, base_shell_operation
):
    """Test writing bash functions"""
    mock_exists.return_value = False
    base_shell_operation._write_bash_functions(MagicMock(), "test content")
    mock_write.assert_called_once_with("test content")


@patch("pathlib.Path.exists")
@patch("pathlib.Path.unlink")
def test_base_shell_operation_remove_bash_functions(
    mock_unlink, mock_exists, base_shell_operation
):
    """Test removing bash functions"""
    mock_exists.return_value = True
    base_shell_operation._remove_bash_functions(MagicMock())
    mock_unlink.assert_called_once()


# Test Shell Command
def test_shell_command_initialization():
    """Test shell command initialization"""
    args = Namespace(
        enable_interactive=False,
        disable_interactive=False,
        enable_persistent_capture=False,
        disable_persistent_capture=False,
        enable_capture=False,
    )
    command = ShellCommand(args)
    assert hasattr(command, "_args")
    assert hasattr(command, "_text_renderer")
    assert hasattr(command, "_warning_renderer")
    assert hasattr(command, "_error_renderer")


@patch("command_line_assistant.commands.shell.ShellOperationFactory")
def test_shell_command_run_success(mock_factory):
    """Test successful shell command execution"""
    args = Namespace(
        enable_interactive=True,
        disable_interactive=False,
        enable_persistent_capture=False,
        disable_persistent_capture=False,
        enable_capture=False,
    )
    mock_operation = MagicMock()
    mock_factory.return_value.create_operation.return_value = mock_operation

    command = ShellCommand(args)
    result = command.run()

    assert result == 0
    mock_operation.execute.assert_called_once()


@patch("command_line_assistant.commands.shell.ShellOperationFactory")
def test_shell_command_run_no_operation(mock_factory):
    """Test shell command with no operation"""
    args = Namespace(
        enable_interactive=False,
        disable_interactive=False,
        enable_persistent_capture=False,
        disable_persistent_capture=False,
        enable_capture=False,
    )
    mock_factory.return_value.create_operation.return_value = None

    command = ShellCommand(args)
    result = command.run()

    assert result == 0


@patch("command_line_assistant.commands.shell.ShellOperationFactory")
def test_shell_command_run_error(mock_factory):
    """Test shell command execution with error"""
    args = Namespace(
        enable_interactive=True,
        disable_interactive=False,
        enable_persistent_capture=False,
        disable_persistent_capture=False,
        enable_capture=False,
    )
    mock_operation = MagicMock()
    mock_operation.execute.side_effect = Exception("Test error")
    mock_factory.return_value.create_operation.return_value = mock_operation

    command = ShellCommand(args)
    result = command.run()

    assert result == 1


# Test Individual Operations
@patch("pathlib.Path.exists")
@patch("pathlib.Path.write_text")
def test_enable_interactive_mode(mock_write, mock_exists, mock_text_renderer):
    """Test enable interactive mode operation"""
    mock_exists.return_value = False
    operation = EnableInteractiveMode(mock_text_renderer, mock_text_renderer)
    operation.execute()
    mock_write.assert_called_once()


@patch("pathlib.Path.exists")
@patch("pathlib.Path.unlink")
def test_disable_interactive_mode(mock_unlink, mock_exists, mock_text_renderer):
    """Test disable interactive mode operation"""
    mock_exists.return_value = True
    operation = DisableInteractiveMode(mock_text_renderer, mock_text_renderer)
    operation.execute()
    mock_unlink.assert_called_once()


@patch("command_line_assistant.commands.shell.start_capturing")
def test_enable_terminal_capture(mock_start_capturing, mock_text_renderer):
    """Test enable terminal capture operation"""
    operation = EnableTerminalCapture(mock_text_renderer, mock_text_renderer)
    operation.execute()
    mock_start_capturing.assert_called_once()


def test_register_subcommand():
    """Test subcommand registration"""
    mock_parser = MagicMock()
    from command_line_assistant.commands.shell import register_subcommand

    register_subcommand(mock_parser)
    mock_parser.add_parser.assert_called_once()
