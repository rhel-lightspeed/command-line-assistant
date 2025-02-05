"""Module to handle the history command."""

import logging
from argparse import Namespace
from pathlib import Path

from command_line_assistant.integrations import BASH_INTERACTIVE
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_text_renderer,
    create_warning_renderer,
)

#: The path to bashrc.d folder
BASH_RC_D_PATH: Path = Path("~/.bashrc.d").expanduser()
#: The complete path to the integration file.
INTEGRATION_FILE: Path = Path(BASH_RC_D_PATH, "cla-interactive.bashrc")

logger = logging.getLogger(__name__)


class ShellCommand(BaseCLICommand):
    """Class that represents the history command."""

    def __init__(self, args: Namespace) -> None:
        """Constructor of the class.

        Note:
            If none of the above is specified, the command will retrieve all
            user history.

        Arguments:
            args (Namespace): The args for that command.
        """
        self._args = args

        self._text_renderer: TextRenderer = create_text_renderer()
        self._warning_renderer: TextRenderer = create_warning_renderer()
        self._error_renderer: TextRenderer = create_error_renderer()

        super().__init__()

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Status code of the execution.
        """
        if self._args.enable_integration:
            return self._write_bash_functions()
        elif self._args.disable_integration:
            return self._remove_bash_functions()

        return 0

    def _write_bash_functions(self) -> int:
        """Internal method to handle the creation of the bash integration file.

        Returns:
            int: The status code of the operation
        """
        if not BASH_RC_D_PATH.exists():
            try:
                BASH_RC_D_PATH.mkdir(0o700)
            except FileExistsError as e:
                logger.debug(
                    "While trying to create the folder at '%s', we got an exception '%s'.",
                    BASH_RC_D_PATH,
                    str(e),
                )

        if INTEGRATION_FILE.exists():
            self._warning_renderer.render(
                f"Integration is already present at {INTEGRATION_FILE}."
            )
            return 0

        try:
            INTEGRATION_FILE.write_text(BASH_INTERACTIVE)
            INTEGRATION_FILE.chmod(0o600)
            self._text_renderer.render(
                f"Integration placed successfully at {INTEGRATION_FILE}"
            )
            return 0
        except FileExistsError as e:
            logger.debug(
                "While trying to write the integration bashrc at '%s', we got the following exception: '%s'",
                str(INTEGRATION_FILE),
                str(e),
            )
            return 1

    def _remove_bash_functions(self) -> int:
        """Internal method to handle the removal of the bash integration file.

        Returns:
            int: The status code of the operation
        """

        if not INTEGRATION_FILE.exists():
            logger.debug(
                "Couldn't find integration file at '%s'", str(INTEGRATION_FILE)
            )
            self._text_renderer.render(
                "It seems that the integration is not enabled. Skipping operation."
            )
            return 0

        try:
            INTEGRATION_FILE.unlink()
            self._text_renderer.render("Integration disabled successfuly.")
            return 0
        except (FileExistsError, FileNotFoundError) as e:
            logger.warning(
                "Got an exception '%s'. Either file is missing or something removed just before this operation",
                str(e),
            )
            return 1


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the root parser.

    Args:
        parser (SubParsersAction): Root parser to register command-specific arguments
    """
    shell_parser = parser.add_parser(
        "shell",
        help="Manage shell integrations",
    )
    shell_parser.add_argument(
        "-ei",
        "--enable-integration",
        action="store_true",
        help="Enable the shell integrations on the system. Currently, only BASH is supported.",
    )
    shell_parser.add_argument(
        "-di",
        "--disable-integration",
        action="store_true",
        help="Disable the shell integrations on the system.",
    )

    shell_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> ShellCommand:
    """Internal command factory to create the command class

    Args:
        args (Namespace): The arguments processed with argparse.

    Returns:
        ShellCommand: Return an instance of class
    """
    return ShellCommand(args)
