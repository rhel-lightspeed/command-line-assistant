import dataclasses
from pathlib import Path
from typing import Union


@dataclasses.dataclass
class LoggingSchema:
    """This class represents the [logging] section of our config.toml file."""

    level: str = "INFO"

    def __post_init__(self) -> None:
        level = self.level.upper()
        allowed_levels = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET")
        if level not in allowed_levels:
            raise ValueError(
                f"The requested level '{level}' is not allowed. Choose from: {', '.join(allowed_levels)}"
            )

        self.level = self.level.upper()


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
class AuthSchema:
    """Internal schema that represents the authentication for clad."""

    cert_file: Path = Path("/etc/pki/consumer/cert.pem")
    key_file: Path = Path("/etc/pki/consumer/key.pem")
    verify_ssl: bool = True

    def __post_init__(self) -> None:
        self.cert_file = Path(self.cert_file)
        self.key_file = Path(self.key_file)


@dataclasses.dataclass
class BackendSchema:
    """This class represents the [backend] section of our config.toml file."""

    endpoint: str = "http://0.0.0.0:8080"
    auth: Union[dict, AuthSchema] = dataclasses.field(default_factory=AuthSchema)

    def __post_init__(self):
        # Auth may be present in the config.toml. If it is not, we odn't do
        # anything and go with defaults.
        if isinstance(self.auth, dict):
            self.auth = AuthSchema(**self.auth)
