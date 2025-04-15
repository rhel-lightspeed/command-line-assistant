from argparse import ArgumentParser, Namespace
from unittest import mock

import pytest

from command_line_assistant.commands import shell
from command_line_assistant.commands.shell import (
    BaseShellOperation,
    DisableInteractiveMode,
    EnableInteractiveMode,
    EnableTerminalCapture,
    ShellCommand,
    _command_factory,
    register_subcommand,
)
from command_line_assistant.exceptions import ShellCommandException
from command_line_assistant.utils.files import NamedFileLock
from command_line_assistant.utils.renderers import create_text_renderer


@pytest.fixture(autouse=True)
def mock_bash_rc(monkeypatch, tmp_path):
    bash_rc_d = tmp_path / ".bashrc.d"
    monkeypatch.setattr(shell, "BASH_RC_D_PATH", bash_rc_d)

    essential_exports_file = tmp_path / "cla-exports.bashrc"
    monkeypatch.setattr(shell, "ESSENTIAL_EXPORTS_FILE", essential_exports_file)

    interactive_mode_integration_file = tmp_path / "cla-interactive.bashrc"
    monkeypatch.setattr(
        shell, "INTERACTIVE_MODE_INTEGRATION_FILE", interactive_mode_integration_file
    )


def test_initialize_bash_folder(default_kwargs, tmp_path):
    bash_rc_d = tmp_path / ".bashrc.d"
    BaseShellOperation(**default_kwargs)._initialize_bash_folder()

    assert oct(bash_rc_d.stat().st_mode).endswith("700")


def test_write_bash_functions(default_kwargs, tmp_path, capsys):
    some_bash_file = tmp_path / "test.bashrc"
    default_kwargs["text_renderer"] = create_text_renderer()
    bash_shell_operation = BaseShellOperation(**default_kwargs)

    bash_shell_operation._write_bash_functions(some_bash_file, "export TEST=1")

    assert some_bash_file.exists()
    assert some_bash_file.read_text() == "export TEST=1"
    captured = capsys.readouterr()
    assert "Integration successfully added at" in captured.out
    assert oct(some_bash_file.stat().st_mode).endswith("600")


def test_write_bash_functions_file_exists(default_kwargs, tmp_path, capsys):
    some_bash_file = tmp_path / "test.bashrc"
    some_bash_file.write_text("export TEST=1")
    default_kwargs["warning_renderer"] = create_text_renderer()
    bash_shell_operation = BaseShellOperation(**default_kwargs)

    bash_shell_operation._write_bash_functions(some_bash_file, "export TEST=1")

    assert some_bash_file.exists()
    assert some_bash_file.read_text() == "export TEST=1"
    captured = capsys.readouterr()
    assert "The integration is already present and enabled" in captured.out


def test_remove_bash_functions(default_kwargs, tmp_path, capsys):
    some_bash_file = tmp_path / "test.bashrc"
    some_bash_file.write_text("export TEST=1")
    default_kwargs["text_renderer"] = create_text_renderer()
    bash_shell_operation = BaseShellOperation(**default_kwargs)

    bash_shell_operation._remove_bash_functions(some_bash_file)

    assert not some_bash_file.exists()
    captured = capsys.readouterr()
    assert "Integration disabled successfully." in captured.out


def test_remove_bash_functions_no_integration_found(default_kwargs, tmp_path, capsys):
    some_bash_file = tmp_path / "test.bashrc"
    default_kwargs["warning_renderer"] = create_text_renderer()
    bash_shell_operation = BaseShellOperation(**default_kwargs)

    bash_shell_operation._remove_bash_functions(some_bash_file)

    assert not some_bash_file.exists()
    captured = capsys.readouterr()
    assert (
        "It seems that the integration is not enabled. Skipping operation."
        in captured.out
    )


@pytest.mark.parametrize(
    ("operation"),
    (
        (EnableInteractiveMode),
        (DisableInteractiveMode),
    ),
)
def test_shell_operations(operation, default_kwargs):
    """Test that all shell operations will work when executed.

    We are calling it this way because all operations are very simply and only
    change the contents and filepath to write. Once we start to make them more
    verbose and complex, we can come back and remove the specific operation
    from the parametrize and make a special test for them. But right now, this
    simple verification should be enough.

    In case there is a failure during the execution, we will catch this
    exception and makr the test as a failed.
    """
    op = operation(**default_kwargs)
    try:
        op.execute()
    except Exception as e:
        pytest.fail(f"We got a failure in {op} with stack: {str(e)}")


@pytest.mark.parametrize(
    ("exception", "expected_msg"),
    ((ShellCommandException("oh no, failure"), "oh no, failure"),),
)
def test_shell_run_exceptions(exception, expected_msg, capsys, monkeypatch):
    monkeypatch.setattr(
        shell.BaseShellOperation,
        "_initialize_bash_folder",
        mock.Mock(side_effect=exception),
    )
    args = Namespace(
        enable_capture=False,
        enable_interactive=True,
        disable_interactive=False,
    )
    result = ShellCommand(args).run()

    captured = capsys.readouterr()
    assert result == 1
    assert expected_msg in captured.err


def test_register_subcommand():
    """Test register_subcommand function"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # Register the subcommand
    register_subcommand(subparsers)

    # Parse a test command
    args = parser.parse_args(["shell", "--enable-interactive"])

    assert args.enable_interactive
    assert hasattr(args, "func")


@pytest.mark.parametrize(
    ("namespace",),
    (
        (
            Namespace(
                enable_capture=False,
                enable_persistent_capture=True,
                disable_persistent_capture=False,
                enable_interactive=False,
                disable_interactive=False,
            ),
        ),
    ),
)
def test_command_factory(namespace):
    """Test _command_factory function"""
    command = _command_factory(namespace)

    assert isinstance(command, ShellCommand)
    assert command._args.enable_capture is False
    assert command._args.enable_persistent_capture is True
    assert command._args.disable_persistent_capture is False
    assert command._args.enable_interactive is False
    assert command._args.disable_interactive is False


def test_enable_terminal_capture(monkeypatch, default_kwargs, capsys):
    default_kwargs["text_renderer"] = create_text_renderer()
    monkeypatch.setattr(shell, "start_capturing", mock.Mock())
    EnableTerminalCapture(**default_kwargs).execute()

    captured = capsys.readouterr()
    assert (
        "Starting terminal reader. Press Ctrl + D to stop the capturing."
        in captured.out
    )


def test_enable_terminal_capture_twice(monkeypatch, default_kwargs):
    default_kwargs["text_renderer"] = create_text_renderer()
    monkeypatch.setattr(shell, "start_capturing", mock.Mock())
    with (
        NamedFileLock(name="terminal"),
        pytest.raises(
            ShellCommandException,
            match="Detected a terminal capture session running with pid",
        ),
    ):
        EnableTerminalCapture(**default_kwargs).execute()


def test_enable_terminal_capture_execution(default_kwargs, monkeypatch):
    """Test that enable terminal capture executes correctly"""
    default_kwargs["text_renderer"] = create_text_renderer()
    monkeypatch.setattr(
        "command_line_assistant.commands.shell.start_capturing", lambda: None
    )
    try:
        operation = EnableTerminalCapture(**default_kwargs)
        operation.execute()
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")
