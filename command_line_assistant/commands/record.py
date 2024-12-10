import logging
import os
import sys

from command_line_assistant.config import Config
from command_line_assistant.handlers import handle_script_session
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction

logger = logging.getLogger(__name__)

# NOTE: This needs more refinement, script session can't be combined with other arguments


class RecordCommand(BaseCLICommand):
    def __init__(self, config: Config) -> None:
        self._config = config
        super().__init__()

    def run(self) -> None:
        enforce_script_session = self._config.output.enforce_script
        output_file = self._config.output.file

        if enforce_script_session and not os.path.exists(output_file):
            logger.error(
                "Please call `%s record` first to initialize script session or create the output file.",
                sys.argv[0],
            )

        handle_script_session(output_file)


def register_subcommand(parser: SubParsersAction, config: Config):
    """
    Register this command to argparse so it's available for the datasets-cli

    Args:
        parser: Root parser to register command-specific arguments
    """
    record_parser = parser.add_parser(
        "record",
        help="Start a recording session for script output.",
    )

    # TODO(r0x0d): This is temporary as it will get removed
    record_parser.set_defaults(func=lambda args: _command_factory(config))


def _command_factory(config: Config) -> RecordCommand:
    return RecordCommand(config)
