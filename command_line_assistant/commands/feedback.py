"""Module to handle the feedback command."""

import argparse
import logging
from argparse import Namespace
from enum import auto
from typing import ClassVar

from command_line_assistant.commands.base import (
    BaseCLICommand,
    BaseOperation,
    CommandOperationFactory,
    CommandOperationType,
)
from command_line_assistant.exceptions import (
    FeedbackCommandException,
)
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import (
    SubParsersAction,
    create_subparser,
)
from command_line_assistant.utils.renderers import (
    create_error_renderer,
)

WARNING_MESSAGE = "Do not include any personal information or other sensitive information in your feedback. Feedback may be used to improve Red Hat's products or services."

logger = logging.getLogger(__name__)


class FeedbackOperationType(CommandOperationType):
    """Enum to control the operations for the command"""

    DEFAULT = auto()


class FeedbackOperationFactory(CommandOperationFactory):
    """Factory for creating feedback operations with decorator-based registration"""

    # Mapping of CLI arguments to operation types
    _arg_to_operation: ClassVar[dict[str, CommandOperationType]] = {
        "submit": FeedbackOperationType.DEFAULT,
    }


class BaseFeedbackOperation(BaseOperation):
    """Base feedback operation common to all operations."""


@FeedbackOperationFactory.register(FeedbackOperationType.DEFAULT)
class DefaultFeedbackOperation(BaseFeedbackOperation):
    """Class to hold the default feedback operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        self.warning_renderer.render(WARNING_MESSAGE)

        feedback_message = "To submit feedback, use the following email address: <cla-feedback@redhat.com>."
        self.text_renderer.render(feedback_message)


class FeedbackCommand(BaseCLICommand):
    """Class that represents the feedback command."""

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Return the status code for the operation
        """
        error_renderer: TextRenderer = create_error_renderer()
        operation_factory = FeedbackOperationFactory()
        try:
            # Get and execute the appropriate operation
            operation = operation_factory.create_operation(
                self._args, self._context, error_renderer=error_renderer
            )
            if operation:
                operation.execute()

            return 0
        except FeedbackCommandException as e:
            logger.info("Failed to execute feedback command: %s", str(e))
            error_renderer.render(f"Failed to execute feedback command: {str(e)}")
            return 1


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the root parser.

    Arguments:
        parser (SubParsersAction): Root parser to register command-specific arguments
    """
    feedback_parser = create_subparser(
        parser,
        "feedback",
        "Submit feedback about Command Line Assistant responses and interactions.",
    )

    feedback_parser.add_argument(
        "--submit",
        action="store_true",
        default=True,
        help=argparse.SUPPRESS,
    )

    feedback_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> FeedbackCommand:
    """Internal command factory to create the command class

    Arguments:
        args (Namespace): The arguments processed with argparse.

    Returns:
        FeedbackCommand: Return an instance of class
    """
    return FeedbackCommand(args)
