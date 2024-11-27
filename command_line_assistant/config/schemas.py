import dataclasses
from pathlib import Path
from typing import Union


@dataclasses.dataclass
class LoggingSchema:
    """This class represents the [logging] section of our config.toml file."""

    verbose: bool = False
    file: Union[str, Path] = Path(  # type: ignore
        "~/.cache/command-line-assistant/command-line-assistant.log"
    )

    def __post_init__(self):
        self.file: Path = Path(self.file).expanduser()


@dataclasses.dataclass
class OutputSchema:
    """This class represents the [output] section of our config.toml file."""

    enforce_script: bool = False
    file: Union[str, Path] = Path("/tmp/command-line-assistant_output.txt")  # type: ignore
    prompt_separator: str = "$"

    def __post_init__(self):
        self.file: Path = Path(self.file).expanduser()


@dataclasses.dataclass
class HistorySchema:
    """This class represents the [history] section of our config.toml file."""

    enabled: bool = True
    file: Union[str, Path] = Path(  # type: ignore
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
