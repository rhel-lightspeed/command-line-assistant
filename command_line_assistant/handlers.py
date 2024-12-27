"""Module to track the handlers for text process."""

import logging
import os
from pathlib import Path

from command_line_assistant.config import Config

logger = logging.getLogger(__name__)


def handle_script_session(command_line_assistant_tmp_file: Path) -> None:
    """Starts a 'script' session and writes the PID to a file, but leaves control of the terminal to the user.

    Args:
        command_line_assistant_tmp_file (Path): Path to the tmp file.
    """
    # Prepare the script command
    script_command = ["script", "-f", str(command_line_assistant_tmp_file)]

    # Start the script session and leave control to the terminal
    os.system(" ".join(script_command))

    # Remove the captured output after the script session ends
    if os.path.exists(command_line_assistant_tmp_file):
        logger.info("Removing %s", command_line_assistant_tmp_file)
        os.remove(command_line_assistant_tmp_file)


def handle_caret(query: str, config: Config) -> str:
    """Replaces caret (^) with command output specified in config file.

    Args:
        query (str): The user provided query
        config (Config): The instance of a config class

    Raises:
        ValueError: In case the output file does not exist.

    Returns:
        str: Context data and the question itself.
    """
    if "^" not in query:
        return query

    captured_output_file = config.output.file

    if not os.path.exists(captured_output_file):
        logger.error(
            "Output file %s does not exist, change location of file in config to use '^'.",
            captured_output_file,
        )
        raise ValueError(f"Output file {captured_output_file} does not exist.")

    prompt_separator = config.output.prompt_separator
    with open(captured_output_file, encoding="utf-8", mode="r") as f:
        # NOTE: takes only last command + output from file
        output = f.read().split(prompt_separator)[-1].strip()

    query = query.replace("^", "")
    query = f"Context data: {output}\nQuestion: " + query
    return query
