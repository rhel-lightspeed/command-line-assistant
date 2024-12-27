"""Module to handle the record command.

Note:
    This needs more refinement, script session can't be combined with other arguments
"""

import logging
from argparse import Namespace
from pathlib import Path

from command_line_assistant.handlers import handle_script_session
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction

logger = logging.getLogger(__name__)


class RecordCommand(BaseCLICommand):
    """Class that represents the record command."""

    def __init__(self, output_file: str) -> None:
        """Constructor of the class.

        Args:
            output_file (str): The file to write the output.
        """
        self._output_file = output_file
        super().__init__()

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Status code of the execution.
        """
        handle_script_session(Path(self._output_file))
        return 0


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the root parser.

    Args:
        parser (SubParsersAction): Root parser to register command-specific arguments
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
    """Internal command factory to create the command class

    Args:
        args (Namespace): The arguments processed with argparse.

    Returns:
        RecordCommand: Return an instance of class
    """
    return RecordCommand(args.output_file)
