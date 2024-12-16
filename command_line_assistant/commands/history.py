import logging
from argparse import Namespace

from dasbus.error import DBusError

from command_line_assistant.dbus.constants import HISTORY_IDENTIFIER
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction

logger = logging.getLogger(__name__)


class HistoryCommand(BaseCLICommand):
    def __init__(self, clear: bool) -> None:
        self._clear = clear
        super().__init__()

    def run(self) -> None:
        proxy = HISTORY_IDENTIFIER.get_proxy()

        if self._clear:
            try:
                logger.info("Cleaning the history.")
                proxy.ClearHistory()
            except DBusError as e:
                logger.info("Failed to clean the history: %s", e)
                raise e


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
