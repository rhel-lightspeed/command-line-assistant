"""Simplified shell command implementation."""

import logging
from argparse import Namespace
from pathlib import Path
from typing import Union

from command_line_assistant.exceptions import ShellCommandException
from command_line_assistant.integrations import BASH_INTERACTIVE
from command_line_assistant.terminal.reader import (
    TERMINAL_CAPTURE_FILE,
    start_capturing,
)
from command_line_assistant.utils.cli import (
    CommandContext,
    argument,
    command,
)
from command_line_assistant.utils.files import NamedFileLock, create_folder, write_file
from command_line_assistant.utils.renderers import RenderUtils

logger = logging.getLogger(__name__)

# Constants
BASH_RC_D_PATH: Path = Path("~/.bashrc.d").expanduser()
INTERACTIVE_MODE_INTEGRATION_FILE: Path = Path(BASH_RC_D_PATH, "cla-interactive.bashrc")
PERSISTENT_TERMINAL_CAPTURE_FILE: Path = Path(
    BASH_RC_D_PATH, "cla-persistent-capture.bashrc"
)
ESSENTIAL_EXPORTS_FILE: Path = Path(BASH_RC_D_PATH, "cla-exports.bashrc")


@command("shell", help="Manage shell integrations")
@argument(
    "--enable-capture",
    action="store_true",
    help="Enable terminal capture for the current terminal session.",
)
@argument(
    "--enable-interactive",
    action="store_true",
    help=(
        "Enable the shell integration for interactive mode on the system. "
        "Currently, only BASH is supported. After the interactive was "
        "sourced, hit Ctrl + G in your terminal to enable interactive mode."
    ),
)
@argument(
    "--disable-interactive",
    action="store_true",
    help="Disable the shell integration for interactive mode on the system.",
)
def shell_command(args: Namespace, context: CommandContext) -> int:
    """Shell command implementation.

    Args:
        args (Namespace): Command-line arguments
        context (CommandContext): Command context

    Returns:
        int: Exit code
    """
    render = RenderUtils(args.plain)

    try:
        # Handle different operations
        if args.enable_interactive:
            return _write_bash_functions(
                render, INTERACTIVE_MODE_INTEGRATION_FILE, BASH_INTERACTIVE
            )
        elif args.disable_interactive:
            return _remove_bash_functions(render, INTERACTIVE_MODE_INTEGRATION_FILE)
        elif args.enable_capture:
            return _enable_capture(render)
        else:
            # If no specific operation is provided, show help-like message
            render.render_warning(
                "No operation specified. Use --help to see available options."
            )
            return 1

    except ShellCommandException as e:
        logger.info("Failed to execute shell command: %s", str(e))
        render.render_error(str(e))
        return e.code


def _write_bash_functions(
    render: RenderUtils, file: Path, contents: Union[bytes, str]
) -> int:
    """Write bash functions to the desired location.

    Args:
        render (RenderUtils): Command utilities instance
        file (Path): The path object with the correct location
        contents (Union[bytes, str]): The contents to be written in the file

    Returns:
        int: The exit code of the operation
    """
    create_folder(BASH_RC_D_PATH)
    if file.exists():
        logger.info("File already exists at %s.", file)
        render.render_warning(
            f"The integration is already present and enabled at {file}! "
            "Restart your terminal or source ~/.bashrc in case it's not working."
        )
        return 2

    # Make an educated guess whether or not the user's bash environment is
    # configured to load files from the bashrc.d folder. If not, print a
    # warning with a suggested solution.
    has_snippet = False
    rc_files = [
        Path(rc).expanduser() for rc in ["~/.bashrc", "~/.bash_profile", "~/.profile"]
    ]
    for rc_file in rc_files:
        try:
            if ".bashrc.d" in rc_file.read_text():
                has_snippet = True
        except FileNotFoundError:
            continue

    if not has_snippet:
        render.render_warning(
            "In order to use shell integration, ensure your ~/.bashrc file loads files from ~/.bashrc.d. See /etc/skel/.bashrc for an example."
        )

    write_file(contents, file)
    render.render_success(
        f"Integration successfully added at {file}. "
        "In order to use it, please restart your terminal or source ~/.bashrc"
    )
    return 0


def _remove_bash_functions(render: RenderUtils, file: Path) -> int:
    """Remove a bash integration.

    Args:
        render (RenderUtils): Command utilities instance
        file (Path): The path object with the correct location

    Returns:
        int: The exit code of the operation
    """
    if not file.exists():
        logger.debug("Couldn't find integration file at '%s'", str(file))
        render.render_warning(
            "It seems that the integration is not enabled. Skipping operation."
        )
        return 2

    try:
        file.unlink()
        render.render_success("Integration disabled successfully.")
    except (FileExistsError, FileNotFoundError) as e:
        logger.warning(
            "Got an exception '%s'. Either file is missing or something removed just before this operation",
            str(e),
        )

    return 0


def _enable_capture(render: RenderUtils) -> int:
    """Enable terminal capture operation.

    Args:
        render (RenderUtils): Command utilities instance

    Returns:
        int: The exit code of the operation
    """
    file_lock = NamedFileLock(name="terminal")

    if file_lock.is_locked:
        raise ShellCommandException(
            f"Detected a terminal capture session running with pid '{file_lock.pid}'."
            " In order to start a new terminal capture session, you must stop the previous one."
        )

    with file_lock:
        render.render_success(
            "Starting terminal reader. Press Ctrl + D to stop the capturing."
        )
        render.render_success(
            f"Terminal capture log is being written to {TERMINAL_CAPTURE_FILE}"
        )
        create_folder(BASH_RC_D_PATH)
        start_capturing()

    return 0
