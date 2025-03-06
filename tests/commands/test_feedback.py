from argparse import ArgumentParser, Namespace
from unittest.mock import patch

import pytest

from command_line_assistant.commands.feedback import (
    DefaultFeedbackOperation,
    FeedbackCommand,
    FeedbackOperationFactory,
    _command_factory,
    register_subcommand,
)
from command_line_assistant.exceptions import FeedbackCommandException
from command_line_assistant.utils.renderers import (
    create_text_renderer,
    create_warning_renderer,
)


def test_default_feedback_operation(default_kwargs, capsys):
    default_kwargs["text_renderer"] = create_text_renderer()
    default_kwargs["warning_renderer"] = create_warning_renderer()

    operation = DefaultFeedbackOperation(**default_kwargs)

    operation.execute()

    captured = capsys.readouterr()

    assert (
        "Please do not include personal information or other sensitive data in\nyour feedback"
        in captured.err.strip()
    )
    assert (
        "Please submit feedback using the following email address"
        in captured.out.strip()
    )


@pytest.mark.parametrize(
    ("operation"),
    (DefaultFeedbackOperation,),
)
def test_feedback_operations(operation, default_kwargs):
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


def test_feedback_run(capsys):
    args = Namespace(
        submit=True,
    )
    result = FeedbackCommand(args).run()

    captured = capsys.readouterr()
    assert result == 0
    assert (
        "Please do not include personal information or other sensitive data in\nyour feedback"
        in captured.err.strip()
    )
    assert (
        "Please submit feedback using the following email address"
        in captured.out.strip()
    )


def test_register_subcommand():
    """Test register_subcommand function"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # Register the subcommand
    register_subcommand(subparsers)

    # Parse a test command
    args = parser.parse_args(["feedback"])

    assert args.submit
    assert hasattr(args, "func")


@pytest.mark.parametrize(
    ("namespace",),
    (
        (
            Namespace(
                submit=True,
            ),
        ),
    ),
)
def test_command_factory(namespace):
    """Test _command_factory function"""
    command = _command_factory(namespace)

    assert isinstance(command, FeedbackCommand)
    assert command._args.submit is True


def test_feedback_command_exception_handling():
    """Test exception handling in the feedback command"""
    args = Namespace(submit=True)
    command = FeedbackCommand(args)

    with patch.object(
        FeedbackOperationFactory,
        "create_operation",
        side_effect=FeedbackCommandException("Test error"),
    ):
        result = command.run()

    assert result == 1  # Should return error code
