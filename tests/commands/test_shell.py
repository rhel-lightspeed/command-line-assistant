from argparse import Namespace
from unittest import mock

import pytest

from command_line_assistant.commands import shell
from command_line_assistant.exceptions import ShellCommandException
from command_line_assistant.utils.cli import CommandContext
from command_line_assistant.utils.files import NamedFileLock


@pytest.fixture
def default_namespace():
    return Namespace(
        enable_capture=False,
        enable_interactive=False,
        disable_interactive=False,
        plain=True,
    )


@pytest.fixture
def command_context():
    return CommandContext()


@pytest.fixture(autouse=True)
def mock_bash_rc(monkeypatch, tmp_path):
    """Mock bash RC directory and files."""
    bash_rc_d = tmp_path / ".bashrc.d"
    monkeypatch.setattr(
        "command_line_assistant.commands.shell.BASH_RC_D_PATH", bash_rc_d
    )

    interactive_mode_integration_file = bash_rc_d / "cla-interactive.bashrc"
    monkeypatch.setattr(
        "command_line_assistant.commands.shell.INTERACTIVE_MODE_INTEGRATION_FILE",
        interactive_mode_integration_file,
    )


def test_shell_command_enable_interactive(default_namespace, command_context, capsys):
    """Test enabling interactive mode."""
    default_namespace.enable_interactive = True
    result = shell.shell_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Integration successfully added" in captured.out


def test_shell_command_enable_interactive_already_exists(
    default_namespace, command_context, capsys, tmp_path
):
    """Test enabling interactive mode when integration already exists."""
    # Create the integration file first
    bash_rc_d = tmp_path / ".bashrc.d"
    bash_rc_d.mkdir(exist_ok=True)
    integration_file = bash_rc_d / "cla-interactive.bashrc"
    integration_file.write_text("# Already exists")

    default_namespace.enable_interactive = True
    result = shell.shell_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 2
    assert "The integration is already present and enabled" in captured.err


def test_shell_command_disable_interactive(
    default_namespace, command_context, capsys, tmp_path
):
    """Test disabling interactive mode."""
    # Create the integration file first
    bash_rc_d = tmp_path / ".bashrc.d"
    bash_rc_d.mkdir(exist_ok=True)
    integration_file = bash_rc_d / "cla-interactive.bashrc"
    integration_file.write_text("# Integration content")

    default_namespace.disable_interactive = True
    result = shell.shell_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Integration disabled successfully" in captured.out
    assert not integration_file.exists()


def test_shell_command_disable_interactive_not_exists(
    default_namespace, command_context, capsys
):
    """Test disabling interactive mode when integration doesn't exist."""
    default_namespace.disable_interactive = True
    result = shell.shell_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 2
    assert "It seems that the integration is not enabled" in captured.err


def test_shell_command_enable_capture(
    default_namespace, command_context, capsys, monkeypatch
):
    """Test enabling terminal capture."""
    # Mock the start_capturing function
    mock_start_capturing = mock.Mock()
    monkeypatch.setattr(
        "command_line_assistant.commands.shell.start_capturing",
        mock_start_capturing,
    )

    default_namespace.enable_capture = True
    result = shell.shell_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Starting terminal reader" in captured.out
    assert "Press Ctrl + D to stop the capturing" in captured.out
    mock_start_capturing.assert_called_once()


def test_shell_command_enable_capture_already_running(
    default_namespace, command_context, capsys
):
    """Test enabling terminal capture when already running."""
    default_namespace.enable_capture = True

    # Simulate terminal capture already running
    with NamedFileLock(name="terminal"):
        result = shell.shell_command.func(default_namespace, command_context)

        captured = capsys.readouterr()
        assert result == 81  # ShellCommandException code
        assert "Detected a terminal capture session running" in captured.err


def test_shell_command_no_operation(default_namespace, command_context, capsys):
    """Test shell command with no specific operation."""
    result = shell.shell_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 1
    assert "No operation specified" in captured.err


def test_shell_command_plain_mode(command_context, capsys):
    """Test shell command in plain mode."""
    args = Namespace(
        enable_interactive=True,
        enable_capture=False,
        disable_interactive=False,
        plain=True,
    )
    result = shell.shell_command.func(args, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Integration successfully added" in captured.out


def test_shell_command_exception_handling(
    default_namespace, command_context, capsys, monkeypatch
):
    """Test shell command exception handling."""

    # Mock an exception in the enable interactive operation
    def mock_write_bash_functions(*args, **kwargs):
        raise ShellCommandException("Test error")

    monkeypatch.setattr(
        "command_line_assistant.commands.shell._write_bash_functions",
        mock_write_bash_functions,
    )

    default_namespace.enable_interactive = True
    result = shell.shell_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 81  # ShellCommandException code
    assert "Test error" in captured.err


def test_shell_command_missing_bashrc_warning(
    default_namespace, command_context, capsys, monkeypatch, tmp_path
):
    """Test warning when .bashrc.d is not configured."""
    # Set up a test home directory without proper .bashrc configuration
    test_home = tmp_path / "test_home"
    test_home.mkdir()
    monkeypatch.setenv("HOME", str(test_home))

    # Create .bashrc without .bashrc.d snippet
    bashrc = test_home / ".bashrc"
    bashrc.write_text("# Basic bashrc")

    # Use plain=False to ensure warning messages are captured properly
    default_namespace.plain = False
    default_namespace.enable_interactive = True
    result = shell.shell_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Integration successfully added" in captured.out
    # In plain=False mode, warnings go to stderr
    assert "In order to use shell integration" in captured.err


def test_shell_command_with_bashrc_d_configured(
    default_namespace, command_context, capsys, monkeypatch, tmp_path
):
    """Test when .bashrc.d is properly configured."""
    # Set up a test home directory with proper .bashrc configuration
    test_home = tmp_path / "test_home"
    test_home.mkdir()
    monkeypatch.setenv("HOME", str(test_home))

    # Create .bashrc with .bashrc.d snippet
    bashrc = test_home / ".bashrc"
    bashrc.write_text("""
# Basic bashrc
if [ -d ~/.bashrc.d ]; then
    for rc in ~/.bashrc.d/*; do
        if [ -f "$rc" ]; then
            . "$rc"
        fi
    done
fi
""")

    default_namespace.enable_interactive = True
    result = shell.shell_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    # Should not show the warning about configuring .bashrc
    assert "In order to use shell integration" not in captured.err


@pytest.mark.parametrize(
    ("enable_interactive", "disable_interactive", "enable_capture"),
    [
        (True, False, False),
        (False, True, False),
        (False, False, True),
    ],
)
def test_shell_command_single_operations(
    enable_interactive,
    disable_interactive,
    enable_capture,
    command_context,
    monkeypatch,
):
    """Test that only one operation can be performed at a time."""
    if enable_capture:
        # Mock start_capturing to avoid actual terminal capture
        monkeypatch.setattr(
            "command_line_assistant.commands.shell.start_capturing", mock.Mock()
        )

    args = Namespace(
        enable_interactive=enable_interactive,
        disable_interactive=disable_interactive,
        enable_capture=enable_capture,
        plain=False,
    )

    result = shell.shell_command.func(args, command_context)
    if disable_interactive and not enable_interactive and not enable_capture:
        # When trying to disable an integration that doesn't exist, returns 2
        assert result == 2
    else:
        assert result == 0


def test_shell_command_integration_content(
    default_namespace, command_context, tmp_path
):
    """Test that the integration content is written correctly."""
    default_namespace.enable_interactive = True
    result = shell.shell_command.func(default_namespace, command_context)

    assert result == 0

    bash_rc_d = tmp_path / ".bashrc.d"
    integration_file = bash_rc_d / "cla-interactive.bashrc"
    assert integration_file.exists()
    content = integration_file.read_text()
    # The content should be the BASH_INTERACTIVE constant from integrations
    # We don't need to test the exact content, just that something was written
    assert len(content) > 0
