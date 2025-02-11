"""Module to handle the history command."""

import logging
from argparse import Namespace
from enum import auto
from pathlib import Path
from typing import ClassVar, Union

from command_line_assistant.commands.base import (
    BaseCLICommand,
    BaseOperation,
    CommandOperationFactory,
    CommandOperationType,
)
from command_line_assistant.exceptions import ShellCommandException
from command_line_assistant.integrations import (
    BASH_ESSENTIAL_EXPORTS,
    BASH_INTERACTIVE,
)
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.terminal.reader import start_capturing
from command_line_assistant.utils.cli import (
    SubParsersAction,
    create_subparser,
)
from command_line_assistant.utils.files import create_folder, write_file
from command_line_assistant.utils.renderers import (
    create_error_renderer,
)

#: The path to bashrc.d folder
BASH_RC_D_PATH: Path = Path("~/.bashrc.d").expanduser()

#: The complete path to the integration file.
INTERACTIVE_MODE_INTEGRATION_FILE: Path = Path(BASH_RC_D_PATH, "cla-interactive.bashrc")

#: The complete path to the persistent terminal capture mode.
PERSISTENT_TERMINAL_CAPTURE_FILE: Path = Path(
    BASH_RC_D_PATH, "cla-persistent-capture.bashrc"
)

#: File to track all the CLA environment variable exports.
ESSENTIAL_EXPORTS_FILE: Path = Path(BASH_RC_D_PATH, "cla-exports.bashrc")

logger = logging.getLogger(__name__)


class ShellOperationType(CommandOperationType):
    """Enum to control the operations for the command"""

    ENABLE_INTERACTIVE = auto()
    DISABLE_INTERACTIVE = auto()
    ENABLE_PERSISTENT_CAPTURE = auto()
    DISABLE_PERSISTENT_CAPTURE = auto()
    ENABLE_CAPTURE = auto()


class ShellOperationFactory(CommandOperationFactory):
    """Factory for creating shell operations with decorator-based registration"""

    # Mapping of CLI arguments to operation types
    _arg_to_operation: ClassVar[dict[str, CommandOperationType]] = {
        "enable_interactive": ShellOperationType.ENABLE_INTERACTIVE,
        "disable_interactive": ShellOperationType.DISABLE_INTERACTIVE,
        "enable_persistent_capture": ShellOperationType.ENABLE_PERSISTENT_CAPTURE,
        "disable_persistent_capture": ShellOperationType.DISABLE_PERSISTENT_CAPTURE,
        "enable_capture": ShellOperationType.ENABLE_CAPTURE,
    }


# Base class for shell operations with common functionality
class BaseShellOperation(BaseOperation):
    """Base shell operation common to all operations."""

    def _initialize_bash_folder(self) -> None:
        """Internal function to initialize the bash folder"""
        # Always ensure essential exports are in place
        create_folder(BASH_RC_D_PATH)
        write_file(BASH_ESSENTIAL_EXPORTS, ESSENTIAL_EXPORTS_FILE)

    def _write_bash_functions(self, file: Path, contents: Union[bytes, str]) -> None:
        """Internal funtion to write the bash function to the desired location

        Arguments:
            file (Path): The path object with the correct location
            contents (Union[bytes, str]): The contents to be written in the file.
        """
        self._initialize_bash_folder()
        if file.exists():
            logger.info("File already exists at %s.", file)
            self.warning_renderer.render(
                f"The integration is already present and enabled at {file}! "
                "Restart your terminal or source ~/.bashrc in case it's not working."
            )
            return

        write_file(contents, file)
        self.text_renderer.render(
            f"Integration successfully added at {file}. "
            "In order to use it, please restart your terminal or source ~/.bashrc"
        )

    def _remove_bash_functions(self, file: Path) -> None:
        """Internal function to remove a bash integration

        Arguments:
            file (Path): The path object with the correct location
        """
        if not file.exists():
            logger.debug("Couldn't find integration file at '%s'", str(file))
            self.warning_renderer.render(
                "It seems that the integration is not enabled. Skipping operation."
            )
            return

        try:
            file.unlink()
            self.text_renderer.render("Integration disabled successfully.")
        except (FileExistsError, FileNotFoundError) as e:
            logger.warning(
                "Got an exception '%s'. Either file is missing or something removed just before this operation",
                str(e),
            )


# Register operations using the decorator
@ShellOperationFactory.register(ShellOperationType.ENABLE_INTERACTIVE)
class EnableInteractiveMode(BaseShellOperation):
    """Class to hold the enable interactive mode operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        self._write_bash_functions(INTERACTIVE_MODE_INTEGRATION_FILE, BASH_INTERACTIVE)


@ShellOperationFactory.register(ShellOperationType.DISABLE_INTERACTIVE)
class DisableInteractiveMode(BaseShellOperation):
    """Class to hold the disable interactive mode operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        self._remove_bash_functions(INTERACTIVE_MODE_INTEGRATION_FILE)


@ShellOperationFactory.register(ShellOperationType.ENABLE_PERSISTENT_CAPTURE)
class EnablePersistentCapture(BaseShellOperation):
    """Class to hold the enable persistent capture more"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        self._write_bash_functions(
            PERSISTENT_TERMINAL_CAPTURE_FILE, BASH_ESSENTIAL_EXPORTS
        )


@ShellOperationFactory.register(ShellOperationType.DISABLE_PERSISTENT_CAPTURE)
class DisablePersistentCapture(BaseShellOperation):
    """Class to the disable persistent capture mode"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        self._remove_bash_functions(PERSISTENT_TERMINAL_CAPTURE_FILE)


@ShellOperationFactory.register(ShellOperationType.ENABLE_CAPTURE)
class EnableTerminalCapture(BaseShellOperation):
    """Class to hold the enable terminal capture operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        self.text_renderer.render(
            "Starting terminal reader. Press Ctrl + D to stop the capturing."
        )
        start_capturing()


class ShellCommand(BaseCLICommand):
    """Class that represents the history command."""

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Return the status code for the operation
        """
        error_renderer: TextRenderer = create_error_renderer()
        operation_factory = ShellOperationFactory()
        try:
            # Get and execute the appropriate operation
            operation = operation_factory.create_operation(
                self._args, self._context, error_renderer=error_renderer
            )
            if operation:
                operation.execute()

            return 0
        except ShellCommandException as e:
            logger.info("Failed to execute shell command: %s", str(e))
            error_renderer.render(f"Failed to execute shell command: {str(e)}")
            return 1


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the root parser.

    Arguments:
        parser (SubParsersAction): Root parser to register command-specific arguments
    """
    shell_parser = create_subparser(parser, "shell", "Manage shell integrations")

    terminal_capture_group = shell_parser.add_argument_group("Terminal Capture Options")
    terminal_capture_group.add_argument(
        "--enable-capture",
        action="store_true",
        help="Enable terminal capture for the current terminal session.",
    )
    terminal_capture_group.add_argument(
        "--enable-persistent-capture",
        action="store_true",
        help="Enable persistent terminal capture for the terminal session.",
    )
    terminal_capture_group.add_argument(
        "--disable-persistent-capture",
        action="store_true",
        help="Disable persistent terminal capture for the terminal session.",
    )

    interactive_mode = shell_parser.add_argument_group("Interactive Mode Options")
    interactive_mode.add_argument(
        "--enable-interactive",
        action="store_true",
        help="Enable the shell integration for interactive mode on the system. Currently, only BASH is supported.",
    )
    interactive_mode.add_argument(
        "--disable-interactive",
        action="store_true",
        help="Disable the shell integrationfor interactive mode on the system.",
    )

    shell_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> ShellCommand:
    """Internal command factory to create the command class

    Arguments:
        args (Namespace): The arguments processed with argparse.

    Returns:
        ShellCommand: Return an instance of class
    """
    return ShellCommand(args)
