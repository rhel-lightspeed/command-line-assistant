import logging
import os
import select
import sys
from pathlib import Path

import yaml


def read_yaml_config(config_file: str) -> dict:
    if not os.path.exists(config_file):
        print(
            f"Config file {config_file} does not exist (use env 'COMMAND_LINE_ASSISTANT_CONFIG' to change destination).",
            file=sys.stderr,
        )
        return {}
    with open(config_file, "r") as f:
        logging.info(f"Reading config file {config_file}")
        return yaml.safe_load(f)


def read_stdin():
    # Check if there's input available on stdin
    if select.select([sys.stdin], [], [], 0.0)[0]:
        # If there is input, read it
        input_data = sys.stdin.read().strip()
        return input_data
    # If no input, return None or handle as you prefer
    return None


def get_payload(query: str) -> dict:
    # Payload "msg" has to have the following structure. It is important that
    # roles of "user" and "assistant" are alternating. Role of "user" is always
    # first.
    # {"role": "user", "content": "tell me about selinux one sentence"},
    # {"role": "assistant", "content": "selinux is really cool."},
    # {"role": "user", "content": "how do I enable selinux?"},
    payload = {"query": query}
    return payload


def expand_user_path(file_path: str) -> Path:
    """Helper method to expand user provided path."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Current file does not exist or was not found: {path}")

    return Path(path).expanduser()
