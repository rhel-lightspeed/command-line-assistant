"""Module to hold the config schema and it's sub schemas."""

import dataclasses
from pathlib import Path
from typing import Optional, Union


@dataclasses.dataclass
class DatabaseSchema:
    """This class represents the [history.database] section of our config.toml file.

    Attributes:
        connection (str): The connection string.
    """

    type: str = "sqlite"  # 'sqlite', 'mysql', 'postgresql', etc.
    host: Optional[str] = None
    database: Optional[str] = None
    port: Optional[int] = None  # Optional for SQLite as it doesn't require host or port
    user: Optional[str] = None  # Optional for SQLite
    password: Optional[str] = None  # Optional for SQLite
    connection_string: Optional[Union[str, Path]] = (
        None  # Some databases like SQLite can use a file path
    )

    def __post_init__(self):
        """Post initialization method to normalize values"""
        # If the database type is not a supported one, we can just skip it.
        allowed_databases = ("mysql", "sqlite", "postgresql")
        if self.type not in allowed_databases:
            raise ValueError(
                f"The database type must be one of {','.join(allowed_databases)}, not {self.type}"
            )

        if self.connection_string:
            self.connection_string = Path(self.connection_string).expanduser()

        # Post-initialization to set default values for specific db types
        if self.type == "sqlite" and not self.connection_string:
            self.connection_string = f"sqlite://{self.database}"
        elif self.type == "mysql" and not self.port:
            self.port = 3306  # Default MySQL port
        elif self.type == "postgresql" and not self.port:
            self.port = 5432  # Default PostgreSQL port

    def get_connection_url(self) -> str:
        """
        Constructs and returns the connection URL or string for the respective database.

        Raises:
            ValueError: In case the type is not recognized

        Returns:
            str: The URL formatted connection
        """
        connection_urls = {
            "sqlite": f"sqlite:///{self.connection_string}",
            "mysql": f"mysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}",
            "postgresql": f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}",
        }

        if self.type not in connection_urls:
            raise ValueError(f"Unsupported database type: {self.type}")

        return connection_urls[self.type]


@dataclasses.dataclass
class LoggingSchema:
    """This class represents the [logging] section of our config.toml file.

    Attributes:
        level (str): The level to log. Defaults to "INFO".
        responses (bool): If the responses should be logged. Defaults to True.
        question (bool): If the questions should be logged. Defaults to True.
        users (dict[str, dict[str, bool]]): A dictionary of users and their logging preferences.
    """

    level: str = "INFO"
    responses: bool = True
    question: bool = True
    users: dict[str, dict[str, bool]] = dataclasses.field(default_factory=dict)

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

    def should_log_for_user(self, username: str, log_type: str) -> bool:
        """Check if logging should be enabled for a specific user and log type.

        Args:
            username (str): The username to check
            log_type (str): The type of log ('responses' or 'question')

        Returns:
            bool: Whether logging should be enabled for this user and log type
        """
        # If user has specific settings, use those
        if username in self.users:
            return self.users[username].get(log_type, False)

        # Otherwise fall back to global settings
        return getattr(self, log_type, False)


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
    database: DatabaseSchema = dataclasses.field(default_factory=DatabaseSchema)

    def __post_init__(self):
        """Post initialization method to normalize values"""

        # # Database may be present in the config.toml. If it is not, we odn't do
        # # anything and go with defaults.
        if isinstance(self.database, dict):
            self.database = DatabaseSchema(**self.database)


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
        self.cert_file = Path(self.cert_file).expanduser()
        self.key_file = Path(self.key_file).expanduser()


@dataclasses.dataclass
class BackendSchema:
    """This class represents the [backend] section of our config.toml file.

    Attributes:
        endpoint (str): The endpoint to communicate with.
        auth (Union[dict, AuthSchema]): The authentication information
    """

    endpoint: str = "http://0.0.0.0:8080"
    auth: AuthSchema = dataclasses.field(default_factory=AuthSchema)

    def __post_init__(self):
        """Post initialization method to normalize values"""
        # Auth may be present in the config.toml. If it is not, we odn't do
        # anything and go with defaults.
        if isinstance(self.auth, dict):
            self.auth = AuthSchema(**self.auth)
