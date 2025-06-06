"""Simplified feedback command implementation."""

import logging
from argparse import Namespace

from command_line_assistant.utils.cli import (
    CommandContext,
    argument,
    command,
)
from command_line_assistant.utils.renderers import RenderUtils

logger = logging.getLogger(__name__)

WARNING_MESSAGE = (
    "Do not include any personal information or other sensitive information in"
    " your feedback. Feedback may be used to improve Red Hat's "
    "products or services."
)


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
    render = RenderUtils(args.plain)

    render.render_warning(WARNING_MESSAGE)

    feedback_message = "To submit feedback, use the following email address: <cla-feedback@redhat.com>."
    render.render_success(feedback_message)

    return 0
