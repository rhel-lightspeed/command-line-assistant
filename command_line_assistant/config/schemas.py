"""Module to hold the config schema and it's sub schemas."""

import dataclasses
from pathlib import Path
from typing import Union


@dataclasses.dataclass
class LoggingSchema:
    """This class represents the [logging] section of our config.toml file.

    Attributes:
        level (str): The level to log. Defaults to "INFO".
    """

    level: str = "INFO"

    def __post_init__(self) -> None:
        """Post initialization method to normalize values

        Raises:
            ValueError: In case the requested level i snot in the allowed_levels list.
        """
        level = self.level.upper()
        allowed_levels = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET")
        if level not in allowed_levels:
            raise ValueError(
                f"The requested level '{level}' is not allowed. Choose from: {', '.join(allowed_levels)}"
            )

        self.level = self.level.upper()


@dataclasses.dataclass
class OutputSchema:
    """This class represents the [output] section of our config.toml file.

    Attributes:
        enforce_script (bool): If the script should be enforced.
        file (Union[str, Path]): The filepath for the script output.
        prompt_separator (str): Define the character for the prompt separator
    """

    enforce_script: bool = False
    file: Union[str, Path] = Path("/tmp/command-line-assistant_output.txt")  # type: ignore
    prompt_separator: str = "$"

    def __post_init__(self):
        """Post initialization method to normalize values"""
        self.file: Path = Path(self.file).expanduser()


@dataclasses.dataclass
class HistorySchema:
    """This class represents the [history] section of our config.toml file.

    Attributes:
        enabled (bool): Define if the history is enabled.
        file (Union[str, Path]): The filepath for the history file
    """

    enabled: bool = True
    file: Union[str, Path] = Path(  # type: ignore
        "/var/lib/command-line-assistant/history.json"
    )

    def __post_init__(self):
        """Post initialization method to normalize values"""
        self.file: Path = Path(self.file).expanduser()


@dataclasses.dataclass
class AuthSchema:
    """Internal schema that represents the authentication for clad.

    Attributes:
        cert_file (Path): The path to the RHSM certificate file
        key_file (Path): The path to the RHSM key file
        verify_ssl (bool): Flag to indicate if the ssl verification is necessary.
    """

    cert_file: Path = Path("/etc/pki/consumer/cert.pem")
    key_file: Path = Path("/etc/pki/consumer/key.pem")
    verify_ssl: bool = True

    def __post_init__(self) -> None:
        """Post initialization method to normalize values"""
        self.cert_file = Path(self.cert_file)
        self.key_file = Path(self.key_file)


@dataclasses.dataclass
class BackendSchema:
    """This class represents the [backend] section of our config.toml file.

    Attributes:
        endpoint (str): The endpoint to communicate with.
        auth (Union[dict, AuthSchema]): The authentication information
    """

    endpoint: str = "http://0.0.0.0:8080"
    auth: Union[dict, AuthSchema] = dataclasses.field(default_factory=AuthSchema)

    def __post_init__(self):
        """Post initialization method to normalize values"""
        # Auth may be present in the config.toml. If it is not, we odn't do
        # anything and go with defaults.
        if isinstance(self.auth, dict):
            self.auth = AuthSchema(**self.auth)
