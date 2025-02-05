from argparse import ArgumentParser, Namespace

import pytest

from command_line_assistant.commands import shell
from command_line_assistant.commands.shell import (
    ShellCommand,
    _command_factory,
    register_subcommand,
)


@pytest.fixture
def default_namespace():
    return Namespace(enable_integration=None, disable_integration=None)


@pytest.fixture(autouse=True)
def mock_bashrc_d_path(tmp_path, monkeypatch):
    bash_rc_d = tmp_path / ".bashrc.d"
    integration_file = bash_rc_d / "cla-interactive.bashrc"
    monkeypatch.setattr(shell, "BASH_RC_D_PATH", bash_rc_d)
    monkeypatch.setattr(shell, "INTEGRATION_FILE", integration_file)


def test_shell_command_initialization(default_namespace):
    """Test QueryCommand initialization"""
    default_namespace.enable_integration = True
    command = ShellCommand(default_namespace)
    assert command._args == default_namespace


def test_register_subcommand():
    """Test register_subcommand function"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # Register the subcommand
    register_subcommand(subparsers)

    # Parse a test command
    args = parser.parse_args(["shell", "--enable-integration"])

    assert args.enable_integration
    assert hasattr(args, "func")


def test_command_factory(default_namespace):
    """Test _command_factory function"""
    default_namespace.enable_integration = True
    command = _command_factory(default_namespace)

    assert isinstance(command, ShellCommand)
    assert command._args.enable_integration


def test_shell_command_enable_integration(capsys, default_namespace):
    """Test QueryCommand run method with different inputs"""
    default_namespace.enable_integration = True
    command = ShellCommand(default_namespace)
    assert command.run() == 0

    # Verify output was printed
    captured = capsys.readouterr()
    assert "Integration placed successfully" in captured.out


def test_shell_command_disable_integration(capsys, default_namespace, tmp_path):
    default_namespace.disable_integration = True
    bash_rc_d = tmp_path / ".bashrc.d"
    integration_file = bash_rc_d / "cla-interactive.bashrc"
    bash_rc_d.mkdir()
    integration_file.write_text("hi!")
    command = ShellCommand(default_namespace)
    assert command.run() == 0

    # Verify output was printed
    captured = capsys.readouterr()
    assert "Integration disabled successfuly." in captured.out


def test_shell_command_enable_integration_file_already_exists(
    capsys, default_namespace, tmp_path, monkeypatch
):
    bash_rc_d = tmp_path / ".bashrc.d"
    integration_file = bash_rc_d / "cla-interactive.bashrc"
    monkeypatch.setattr(shell, "BASH_RC_D_PATH", bash_rc_d)
    monkeypatch.setattr(shell, "INTEGRATION_FILE", integration_file)
    bash_rc_d.mkdir()
    integration_file.write_text("hi!")

    default_namespace.enable_integration = True
    command = ShellCommand(default_namespace)
    assert command.run() == 0

    # Verify output was printed
    captured = capsys.readouterr()
    assert "Integration is already present" in captured.err
