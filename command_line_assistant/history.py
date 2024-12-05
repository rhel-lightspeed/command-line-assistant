import json
import logging
from pathlib import Path

from command_line_assistant.config import Config


def handle_history_read(config: Config) -> list:
    """
    Reads the history from a file and returns it as a list of dictionaries.
    """
    if not config.history.enabled:
        return []

    filepath = config.history.file
    if not filepath or not filepath.exists():
        logging.warning("History file %s does not exist.", filepath)
        logging.warning("File will be created with first response.")
        return []

    max_size = config.history.max_size
    history = []
    try:
        data = filepath.read_text()
        history = json.loads(data)
    except json.JSONDecodeError as e:
        logging.error("Failed to read history file %s: %s", filepath, e)
        return []

    logging.info("Taking maximum of %s entries from history.", max_size)
    return history[:max_size]


def handle_history_write(history_file: Path, history: list, response: str) -> None:
    """
    Writes the history to a file.
    """

    if not history_file.exists():
        history_file.parent.mkdir(mode=0o755)

    history.append({"role": "assistant", "content": response})

    try:
        data = json.dumps(history)
        history_file.write_text(data)
    except json.JSONDecodeError as e:
        logging.error("Failed to write history file %s: %s", history_file, e)
