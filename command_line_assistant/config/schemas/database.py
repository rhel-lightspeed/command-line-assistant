"""Schemas for the database config."""

import dataclasses
import os
from pathlib import Path
from typing import Optional, Union

#: Name of the credential containing the username to be loaded
SYSTEMD_USERNAME_ID: str = "database-username"
#: Name of the credential containing the password to be loaded
SYSTEMD_PASSWORD_ID: str = "database-password"

#: Tuple containing the allowed databases types
ALLOWED_DATABASES = ("sqlite", "mysql", "postgresql")


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
        type (str): The database type to connect
        host (Optional[str], optioanl): The host for the database
        database (Optional[str], optioanl): The name for the database
        port (Optional[int], optioanl): The port of the database
        username (Optional[str], optioanl): The username to connect
        password (Optional[str], optioanl): The password to connect
        connection_string (Optional[Union[str, Path]], optioanl): Database path for sqlite
    """

    type: str = "sqlite"  # 'sqlite', 'mysql', 'postgresql', etc.
    host: Optional[str] = None  # noqa: F821
    database: Optional[str] = None
    port: Optional[int] = None  # Optional for SQLite as it doesn't require host or port
    username: Optional[str] = None  # Optional for SQLite
    password: Optional[str] = None  # Optional for SQLite
    connection_string: Optional[Union[str, Path]] = (
        None  # Some databases like SQLite can use a file path
    )

    def __post_init__(self):
        """Post initialization method to normalize values"""
        # If the database type is not a supported one, we can just skip it.
        if self.type not in ALLOWED_DATABASES:
            raise ValueError(
                f"The database type must be one of {', '.join(ALLOWED_DATABASES)}, not {self.type}"
            )

        if self.connection_string:
            self.connection_string = Path(self.connection_string).expanduser()

        # Special handle for MySQL and PostgreSQL credentials
        if self.type in ALLOWED_DATABASES[1:]:
            if not self.username:
                self.username = self._read_credentials_from_systemd(SYSTEMD_USERNAME_ID)

            if not self.password:
                self.password = self._read_credentials_from_systemd(SYSTEMD_PASSWORD_ID)

    def _read_credentials_from_systemd(self, identifier: str) -> str:
        """Read the credentials from systemd folder.

        Note:
            This should only happen in case the username/password is not
            defined in the config file. This is a more secure way for the user
            to specify their credentials without relying on writing it
            un-encrypted in a configuration file.

        Arguments:
            identifier (str): The identifier to be read from systemd
            credentials directory.

        Raises:
            ValueError: In case the `CREDENTIALS_DIRECTORY` is not present or
            the credential file is empty.
        """
        systemd_credentials_dir = os.getenv("CREDENTIALS_DIRECTORY", None)
        if not systemd_credentials_dir:
            raise ValueError(
                "Either username or password is missing from config file or systemd-creds."
            )

        credentials_file = Path(systemd_credentials_dir, identifier)

        try:
            return credentials_file.read_text()
        except FileNotFoundError as e:
            raise ValueError(
                f"The credential file at '{credentials_file}' does not exist."
            ) from e

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
            "mysql": f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}",
            "postgresql": f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}",
        }

        return connection_urls[self.type]
