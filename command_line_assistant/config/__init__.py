"""Main configuration module."""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path

from command_line_assistant.config.schemas import (
    BackendSchema,
    HistorySchema,
    LoggingSchema,
    OutputSchema,
)
from command_line_assistant.utils.environment import get_xdg_config_path

# tomllib is available in the stdlib after Python3.11. Before that, we import
# from tomli.
try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:
    import tomli as tomllib  # pyright: ignore[reportMissingImports]


#: Define the config file path.
CONFIG_FILE_DEFINITION: tuple[str, str] = (
    "command-line-assistant",
    "config.toml",
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class Config:
    """Class that holds our configuration file representation.

    With this class, after being initialized, one can access their fields like:

    >>> config = Config()
    >>> config.output.enforce_script

    Attributes:
        output (OutputSchema): Match the `py:OutputSchema` class and their fields
        history (HistorySchema): Match the `py:HistorySchema` class and their fields
        backend (BackendSchema): Match the `py:BackendSchema` class and their fields
        logging (LoggingSchema): Match the `py:LoggingSchema` class and their fields
    """

    output: OutputSchema = dataclasses.field(default_factory=OutputSchema)
    history: HistorySchema = dataclasses.field(default_factory=HistorySchema)
    backend: BackendSchema = dataclasses.field(default_factory=BackendSchema)
    logging: LoggingSchema = dataclasses.field(default_factory=LoggingSchema)


def load_config_file() -> Config:
    """Load the configuration file from the system.

    Raises:
        FileNotFoundError: In case the configuration file is missing
        tomllib.TOMLDecodeError: In case it is not possible to decode the config file

    Returns:
        Config: An instance of the configuration file
    """
    config_dict = {}
    config_file_path = Path(get_xdg_config_path(), *CONFIG_FILE_DEFINITION)

    try:
        print(f"Loading configuration file from {config_file_path}")
        data = config_file_path.read_text()
        config_dict = tomllib.loads(data)
    except (FileNotFoundError, tomllib.TOMLDecodeError) as ex:
        logger.error(ex)
        raise ex

    return Config(
        output=OutputSchema(**config_dict["output"]),
        history=HistorySchema(**config_dict["history"]),
        backend=BackendSchema(**config_dict["backend"]),
        logging=LoggingSchema(**config_dict["logging"]),
    )
