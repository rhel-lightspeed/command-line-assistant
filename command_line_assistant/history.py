import json
import logging

from command_line_assistant.config import Config


def handle_history_read(config: Config) -> dict:
    """
    Reads the history from a file and returns it as a list of dictionaries.
    """
    if not config.history.enabled:
        return []

    filepath = config.history.file
    if not filepath or not filepath.exists():
        logging.warning(f"History file {filepath} does not exist.")
        logging.warning("File will be created with first response.")
        return []

    max_size = config.history.max_size
    history = []
    try:
        data = filepath.read_text()
        history = json.loads(data)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to read history file {filepath}: {e}")
        return []

    logging.info(f"Taking maximum of {max_size} entries from history.")
    return history[:max_size]


def handle_history_write(config: Config, history: list, response: str) -> None:
    """
    Writes the history to a file.
    """
    if not config.history.enabled:
        return

    filepath = config.history.file
    filepath.makedirs(mode=0o755)

    if response:
        history.append({"role": "assistant", "content": response})

    try:
        data = json.dumps(history)
        filepath.write_text(data)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to write history file {filepath}: {e}")
