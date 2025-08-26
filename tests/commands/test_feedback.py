from argparse import Namespace

import pytest

from command_line_assistant.commands import feedback
from command_line_assistant.commands.cli import CommandContext


@pytest.fixture
def default_namespace():
    return Namespace(
        submit=True,
        plain=True,
    )


@pytest.fixture
def command_context():
    return CommandContext()


@pytest.fixture
def disable_stream_flush(monkeypatch):
    """Fixture to make StreamWriter use current sys.stdout and disable flushing."""
    import sys

    from command_line_assistant.rendering.stream import StreamWriter

    # Patch StreamWriter to use current sys.stdout and disable flushing
    original_init = StreamWriter.__init__

    def patched_init(self, stream=None, flush_on_write=True, theme=None):
        # Always use current sys.stdout and disable flushing
        original_init(self, stream=sys.stdout, flush_on_write=False, theme=theme)

    monkeypatch.setattr(StreamWriter, "__init__", patched_init)
    yield


def test_feedback_command_success(
    default_namespace, command_context, capsys, disable_stream_flush
):
    """Test feedback command executes successfully."""

    result = feedback.feedback_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Do not include any personal information" in captured.out
    assert (
        "To submit feedback, use the following email address: <cla-feedback@redhat.com>"
        in captured.out
    )


def test_feedback_command_plain_mode(command_context, capsys, disable_stream_flush):
    """Test feedback command in plain mode."""

    args = Namespace(submit=True, plain=True)
    result = feedback.feedback_command.func(args, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "Do not include any personal information" in captured.out
    assert "cla-feedback@redhat.com" in captured.out


def test_feedback_command_submit_false(command_context, capsys, disable_stream_flush):
    """Test feedback command with submit=False (should still work since it's default action)."""

    args = Namespace(submit=False, plain=False)
    result = feedback.feedback_command.func(args, command_context)

    captured = capsys.readouterr()
    assert result == 0
    assert "cla-feedback@redhat.com" in captured.out


def test_feedback_command_warning_message_content(
    default_namespace, command_context, capsys, disable_stream_flush
):
    """Test that the warning message contains expected content."""

    feedback.feedback_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    warning_output = captured.out

    # Check key parts of the warning message
    assert "Do not include any personal information" in warning_output
    assert "other sensitive information" in warning_output
    assert "in your feedback" in warning_output
    assert "may be used to improve Red Hat's products or services" in warning_output


def test_feedback_command_success_message_content(
    default_namespace, command_context, capsys, disable_stream_flush
):
    """Test that the success message contains expected content."""

    feedback.feedback_command.func(default_namespace, command_context)

    captured = capsys.readouterr()
    success_output = captured.out

    # Check the feedback email message
    assert "To submit feedback" in success_output
    assert "cla-feedback@redhat.com" in success_output
