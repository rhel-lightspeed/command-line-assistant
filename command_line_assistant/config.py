import json
import logging
from collections import namedtuple
from pathlib import Path

# tomllib is available in the stdlib after Python3.11. Before that, we import
# from tomli.
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from command_line_assistant import utils

CONFIG_DEFAULT_PATH: Path = Path("~/.config/shellai/config.toml")

# tomllib does not support writting files, so we will create our own.
CONFIG_TEMPLATE = """\
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


class OutputSchema(
    namedtuple("Output", ["enforce_script", "file", "prompt_separator"])
):
    """This class represents the [output] section of our config.toml file."""

    # Locking down against extra fields at runtime
    __slots__ = ()

    # We are overriding __new__ here because namedtuple only offers default values to fields from Python 3.7+
    def __new__(
        cls,
        enforce_script: bool = False,
        file: str = "/tmp/shellai_output.txt",
        prompt_separator: str = "$",
    ):
        file = utils.expand_user_path(file)
        return super(OutputSchema, cls).__new__(
            cls, enforce_script, file, prompt_separator
        )


class HistorySchema(namedtuple("History", ["enabled", "file", "max_size"])):
    """This class represents the [history] section of our config.toml file."""

    # Locking down against extra fields at runtime
    __slots__ = ()

    # We are overriding __new__ here because namedtuple only offers default values to fields from Python 3.7+
    def __new__(
        cls,
        enabled: bool = True,
        file: str = "~/.local/share/shellai/shellai_history.json",
        max_size: int = 100,
    ):
        file = utils.expand_user_path(file)
        return super(HistorySchema, cls).__new__(cls, enabled, file, max_size)


class BackendSchema(namedtuple("Backend", ["endpoint"])):
    """This class represents the [backend] section of our config.toml file."""

    # Locking down against extra fields at runtime
    __slots__ = ()

    # We are overriding __new__ here because namedtuple only offers default values to fields from Python 3.7+
    def __new__(
        cls,
        endpoint: str = "http://0.0.0.0:8080/v1/query/",
    ):
        return super(BackendSchema, cls).__new__(cls, endpoint)


class Config:
    """Class that holds our configuration file representation.

    With this class, after being initialized, one can access their fields like:

    >>> config = Config()
    >>> config.output.enforce_script

    The currently available top-level fields are:
        * output = Match the `py:Output` class and their fields
        * history = Match the `py:History` class and their fields
        * backend = Match the `py:backend` class and their fields
    """

    def __init__(self, output: dict, history: dict, backend: dict) -> None:
        self.output: OutputSchema = OutputSchema(**output)
        self.history: HistorySchema = HistorySchema(**history)
        self.backend: BackendSchema = BackendSchema(**backend)


def _create_config_file(config_file: Path) -> None:
    """Create a new configuration file with default values."""

    logging.info(f"Creating new config file at {config_file.parent}")
    config_file.parent.mkdir(mode=0o755)
    base_config = Config(
        OutputSchema()._asdict(), HistorySchema()._asdict(), BackendSchema()._asdict()
    )

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
    config_file.write_text(config_formatted)


def _read_config_file(config_file: Path) -> Config:
    """Read configuration file."""
    config_dict = {}
    try:
        data = config_file.read_text()
        config_dict = tomllib.loads(data)
    except FileNotFoundError as ex:
        logging.error(ex)

    return Config(
        output=config_dict["output"],
        history=config_dict["history"],
        backend=config_dict["backend"],
    )


def load_config_file(config_file: Path) -> Config:
    """Load configuration file for shellai.

    If the user specifies a path where no config file is located, we will create one with default values.
    """
    if not config_file.exists():
        _create_config_file(config_file)

    return _read_config_file(config_file)
