from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path
from typing import ClassVar

# tomllib is available in the stdlib after Python3.11. Before that, we import
# from tomli.
try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:
    import tomli as tomllib  # pyright: ignore[reportMissingImports]


CONFIG_DEFAULT_PATH: Path = Path("~/.config/command-line-assistant/config.toml")

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
verify_ssl = {verify_ssl}

[logging]
type = "{logging_type}"
"""


@dataclasses.dataclass
class LoggingSchema:
    """This class represents the [logging] section of our config.toml file."""

    _logging_types: ClassVar[tuple[str, str]] = (
        "verbose",
        "minimal",
    )
    type: str = "minimal"
    file: str | Path = Path(  # type: ignore
        "~/.cache/command-line-assistant/command-line-assistant.log"
    )

    def _validate_logging_type(self, type: str):
        if type not in self._logging_types:
            raise TypeError(
                f"Logging type {type} is not available. Please, choose from {(',').join(self._logging_types)}"
            )

    def __post_init__(self):
        self.file: Path = Path(self.file).expanduser()


@dataclasses.dataclass
class OutputSchema:
    """This class represents the [output] section of our config.toml file."""

    enforce_script: bool = False
    file: str | Path = Path("/tmp/command-line-assistant_output.txt")  # type: ignore
    prompt_separator: str = "$"

    def __post_init__(self):
        self.file: Path = Path(self.file).expanduser()


@dataclasses.dataclass
class HistorySchema:
    """This class represents the [history] section of our config.toml file."""

    enabled: bool = True
    file: str | Path = Path(  # type: ignore
        "~/.local/share/command-line-assistant/command-line-assistant_history.json"
    )
    max_size: int = 100

    def __post_init__(self):
        self.file: Path = Path(self.file).expanduser()


@dataclasses.dataclass
class BackendSchema:
    """This class represents the [backend] section of our config.toml file."""

    endpoint: str = "http://0.0.0.0:8080/v1/query"
    verify_ssl: bool = True


@dataclasses.dataclass
class Config:
    """Class that holds our configuration file representation.

    With this class, after being initialized, one can access their fields like:

    >>> config = Config()
    >>> config.output.enforce_script

    The currently available top-level fields are:
        * output = Match the `py:OutputSchema` class and their fields
        * history = Match the `py:HistorySchema` class and their fields
        * backend = Match the `py:BackendSchema` class and their fields
        * logging = Match the `py:LoggingSchema` class and their fields
    """

    output: OutputSchema = dataclasses.field(default_factory=OutputSchema)
    history: HistorySchema = dataclasses.field(default_factory=HistorySchema)
    backend: BackendSchema = dataclasses.field(default_factory=BackendSchema)
    logging: LoggingSchema = dataclasses.field(default_factory=LoggingSchema)


def _create_config_file(config_file: Path) -> None:
    """Create a new configuration file with default values."""

    logging.info("Creating new config file at %s", config_file.parent)
    config_file.parent.mkdir(mode=0o755)
    base_config = Config()

    mapping = {
        "enforce_script": json.dumps(base_config.output.enforce_script),
        "output_file": base_config.output.file,
        "prompt_separator": base_config.output.prompt_separator,
        "enabled": json.dumps(base_config.history.enabled),
        "history_file": base_config.history.file,
        "max_size": base_config.history.max_size,
        "endpoint": base_config.backend.endpoint,
        "verify_ssl": json.dumps(base_config.backend.verify_ssl),
        "logging_type": base_config.logging.type,
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
        output=OutputSchema(**config_dict["output"]),
        history=HistorySchema(**config_dict["history"]),
        backend=BackendSchema(**config_dict["backend"]),
        logging=LoggingSchema(**config_dict["logging"]),
    )


def load_config_file(config_file: Path) -> Config:
    """Load configuration file for command-line-assistant.

    If the user specifies a path where no config file is located, we will create one with default values.
    """
    if not config_file.exists():
        _create_config_file(config_file)

    return _read_config_file(config_file)
