"""Terminal module to hold the parsing functions and constants."""

import json
import logging
import re

from command_line_assistant.terminal.reader import OUTPUT_FILE_NAME

#: The compiled regex to clean the ANSI escape sequence
ANSI_ESCAPE_SEQ = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


logger = logging.getLogger(__name__)


def parse_terminal_output() -> list[dict[str, str]]:
    """Parse collected terminal output.

    Returns:
        list[dict[str, str]]: A reversed list containing the parsed data. If no
        file was found, we just return empty list.
    """
    result = []

    if not OUTPUT_FILE_NAME.exists():
        return result

    with OUTPUT_FILE_NAME.open(mode="r") as handler:
        for block in handler:
            logger.debug("Parsing block %s", block)
            # Parse the JSON
            try:
                parsed = json.loads(block)
                parsed["command"] = clean_parsed_text(parsed["command"])
                parsed["output"] = clean_parsed_text(parsed["output"])
                # Just ignore the exit at the end.
                if parsed["output"].endswith("exit"):
                    continue
                result.append(parsed)
            except json.JSONDecodeError as e:
                logger.info(
                    "Couldn't deserialize the json output. Returning empty list. %s",
                    str(e),
                )
                return result

    logger.debug("Final result json list: %s", result)
    # Reverse the list before returning
    result.reverse()
    return result


def find_output_by_index(index: int, output: list) -> str:
    """Find a given output from the parsed output list with index.

    Arguments:
        index (int): The index to be accessed from the list
        output (list): The output list to be searched.

    Returns:
        str: In case it finds the output, otherwise, empty string.
    """
    logger.info("Checking for output with index %s", index)
    try:
        return output[index]["output"]
    except (IndexError, KeyError):
        logger.warning("Couldn't find a match for index %s", index)
        return ""


def clean_parsed_text(text: str) -> str:
    """Clean the parsed text.

    Note:
        This will remove ANSI escape sequences and newline/returnlines feeds.

    Returns:
        str: The cleaned string.
    """
    # Remove ANSI escape sequences
    logger.info("Cleaning ANSI escape sequences with regex %s", ANSI_ESCAPE_SEQ)
    cleaned_ansi_escape_seq = ANSI_ESCAPE_SEQ.sub("", text)
    return cleaned_ansi_escape_seq.strip()
