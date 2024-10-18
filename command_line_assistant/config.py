import json
import logging
import os
from collections import namedtuple

try:
    import tomllib
except ImportError:
    # Needed for versions below RHEL 10.
    import tomli as tomllib

CONFIG_DEFAULT_PATH: str = "~/.config/shellai/config.toml"

# tomllib does not support writting files, so we will create our own.
CONFIG_TEMPLATE = """
[output]
# otherwise recording via script session will be enforced
enforce_script = {enforce_script}
# file with output(s) of regular commands (e.g. ls, echo, etc.)
file = "{output_file}"
# Keep non-empty if your file contains only output of commands (not prompt itself)
prompt_separator = "{prompt_separator}"

[history]
enabled = {enabled}
file = "{history_file}"
# max number of queries in history (including responses)
max_size = {max_size}

[backend]
endpoint = "{endpoint}"

"""


class Output(namedtuple("Output", ["enforce_script", "file", "prompt_separator"])):
    __slots__ = ()

    def __new__(
        cls,
        enforce_script: bool = False,
        file: str = "/tmp/shellai_output.txt",
        prompt_separator: str = "$",
    ):
        return super(Output, cls).__new__(cls, enforce_script, file, prompt_separator)


class History(namedtuple("History", ["enabled", "file", "max_size"])):
    __slots__ = ()

    def __new__(
        cls,
        enabled: bool = True,
        file: str = "/tmp/shellai_output.txt",
        max_size: int = 100,
    ):
        return super(History, cls).__new__(cls, enabled, file, max_size)


class Backend(namedtuple("Backend", ["endpoint"])):
    endpoint: str = "http://0.0.0.0:8080/v1/query/"
    __slots__ = ()

    def __new__(
        cls,
        endpoint: str = "http://0.0.0.0:8080/v1/query/",
    ):
        return super(Backend, cls).__new__(cls, endpoint)


class Config:
    def __init__(self, output: dict, history: dict, backend: dict) -> None:
        self.output: Output = Output(**output)
        self.history: History = History(**history)
        self.backend: Backend = Backend(**backend)


def _create_config_file(config_path: str) -> None:
    """Create a new configuration file with default values."""
    config_dir = os.path.dirname(config_path)
    logging.info(f"Creating new config file at {config_path}")
    os.makedirs(config_dir, mode=0o755, exist_ok=True)
    base_config = Config(Output()._asdict(), History()._asdict(), Backend()._asdict())

    with open(config_path, mode="w") as handler:
        mapping = {
            "enforce_script": json.dumps(base_config.output.enforce_script),
            "output_file": base_config.output.file,
            "prompt_separator": base_config.output.prompt_separator,
            "enabled": json.dumps(base_config.history.enabled),
            "history_file": base_config.history.file,
            "max_size": base_config.history.max_size,
            "endpoint": base_config.backend.endpoint,
        }
        config_formatted = CONFIG_TEMPLATE.format_map(mapping)
        handler.write(config_formatted)


def _read_config_file(config_path: str) -> Config:
    """Read configuration file."""
    config_dict = {}
    try:
        with open(config_path, mode="rb") as handler:
            config_dict = tomllib.load(handler)
    except FileNotFoundError as ex:
        logging.error(ex)

    # Normalize filepaths
    config_dict["history"]["file"] = os.path.expanduser(config_dict["history"]["file"])
    config_dict["output"]["file"] = os.path.expanduser(config_dict["output"]["file"])

    return Config(
        output=config_dict["output"],
        history=config_dict["history"],
        backend=config_dict["backend"],
    )


def load_config_file(config_path: str) -> Config:
    """Load configuration file for shellai.

    If the user specifies a path where no config file is located, we will create one with default values.
    """
    config_file = os.path.expanduser(config_path)
    # Handle case where the user initiates a config file in current dir.
    if not os.path.dirname(config_file):
        config_file = os.path.join(os.path.curdir, config_file)

    if not os.path.exists(config_file):
        _create_config_file(config_file)

    return _read_config_file(config_file)
