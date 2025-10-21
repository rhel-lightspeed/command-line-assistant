"""Module to handle the feedback command."""

import logging
from argparse import Namespace

from command_line_assistant.commands.cli import CommandContext, argument, command
from command_line_assistant.rendering.renderers import Renderer
from command_line_assistant.rendering.theme import load_theme

logger = logging.getLogger(__name__)


@command(
    "feedback",
    help="Submit feedback about the Command Line Assistant responses and interactions.",
)
@argument(
    "--submit",
    action="store_true",
    default=True,
    help="Submit feedback (default action)",
)
def feedback_command(args: Namespace, context: CommandContext) -> int:
    """Feedback command implementation."""
    render = Renderer(args.plain, theme=load_theme())

    render.notice(
        "Do not include any personal information or other"
        " sensitive information in your feedback. Feedback may"
        " be used to improve Red Hat's products or services."
    )

    feedback_message = "To submit feedback, use the following email address: <cla-feedback@redhat.com>."
    render.normal(feedback_message)

    return 0
