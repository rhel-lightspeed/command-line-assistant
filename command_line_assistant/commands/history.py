import logging
from argparse import Namespace
from pathlib import Path

from command_line_assistant.history import handle_history_write
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction

logger = logging.getLogger(__name__)


class HistoryCommand(BaseCLICommand):
    def __init__(self, clear: bool) -> None:
        self._clear = clear
        super().__init__()

    def run(self) -> None:
        if self._clear:
            logger.info("Clearing history of conversation")
            # TODO(r0x0d): Rewrite this.
            handle_history_write(Path("/tmp/test_history.json"), [], "")


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the datasets-cli

    Args:
        parser: Root parser to register command-specific arguments
    """
    history_parser = parser.add_parser(
        "history",
        help="Manage conversation history",
    )
    history_parser.add_argument(
        "--clear", action="store_true", help="Clear the history."
    )
    history_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> HistoryCommand:
    return HistoryCommand(args.clear)
