import logging
from argparse import Namespace
from pathlib import Path

from command_line_assistant.handlers import handle_script_session
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction

logger = logging.getLogger(__name__)

# NOTE: This needs more refinement, script session can't be combined with other arguments


class RecordCommand(BaseCLICommand):
    def __init__(self, output_file: str) -> None:
        self._output_file = output_file
        super().__init__()

    def run(self) -> int:
        handle_script_session(Path(self._output_file))
        return 0


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the datasets-cli

    Args:
        parser: Root parser to register command-specific arguments
    """
    record_parser = parser.add_parser(
        "record",
        help="Start a recording session for script output.",
    )
    record_parser.add_argument(
        "--output-file", help="The place where to store the output file."
    )

    record_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> RecordCommand:
    return RecordCommand(args.output_file)
