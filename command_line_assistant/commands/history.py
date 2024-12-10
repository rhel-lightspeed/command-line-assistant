import logging
from argparse import Namespace

from command_line_assistant.config import Config
from command_line_assistant.history import handle_history_write
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction

logger = logging.getLogger(__name__)


class HistoryCommand(BaseCLICommand):
    def __init__(self, clear: bool, config: Config) -> None:
        self._clear = clear
        self._config = config
        super().__init__()

    def run(self) -> None:
        if self._clear:
            logger.info("Clearing history of conversation")
            handle_history_write(self._config, [], "")


def register_subcommand(parser: SubParsersAction, config: Config):
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

    # TODO(r0x0d): This is temporary as it will get removed
    history_parser.set_defaults(func=lambda args: _command_factory(args, config))


def _command_factory(args: Namespace, config: Config) -> HistoryCommand:
    return HistoryCommand(args.clear, config)
