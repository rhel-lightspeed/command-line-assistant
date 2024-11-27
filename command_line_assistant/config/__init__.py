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

# tomllib is available in the stdlib after Python3.11. Before that, we import
# from tomli.
try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:
    import tomli as tomllib  # pyright: ignore[reportMissingImports]


CONFIG_DEFAULT_PATH: Path = Path(
    "~/Workspace/command-line-assistant/config.toml"
).expanduser()

# TODO(r0x0d): Move this to the command-line-assistant.spec
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
verbose = {logging_verbose}
"""


@dataclasses.dataclass(frozen=True)
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


def load_config_file() -> Config:
    """Read configuration file."""

    config_dict = {}

    try:
        data = CONFIG_DEFAULT_PATH.read_text()
        config_dict = tomllib.loads(data)
    except (FileNotFoundError, tomllib.TOMLDecodeError) as ex:
        logging.error(ex)
        raise ex

    return Config(
        output=OutputSchema(**config_dict["output"]),
        history=HistorySchema(**config_dict["history"]),
        backend=BackendSchema(**config_dict["backend"]),
        logging=LoggingSchema(**config_dict["logging"]),
    )
