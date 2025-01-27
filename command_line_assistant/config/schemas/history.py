"""Schemas for the history config."""

import dataclasses
from pathlib import Path
from typing import Optional, Union


# TODO(r0x0d): Abstract this in the future to be it's own config and not tied to History.
@dataclasses.dataclass
class DatabaseSchema:
    """This class represents the [history.database] section of our config.toml file.

    Notes:
        If you are running MySQL or MariaDB in a container and want to test it
        out, don't set the host to "localhost", but set it to "127.0.0.1". The
        "localhost" will use the mysql socket connector, and "127.0.0.1" will
        use TCP connector.

        Reference: https://stackoverflow.com/a/4448568

    Attributes:
        connection (str): The connection string.
    """

    type: str = "sqlite"  # 'sqlite', 'mysql', 'postgresql', etc.
    host: Optional[str] = None  # noqa: F821
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
