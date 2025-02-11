"""Schemas for the backend config."""

import dataclasses
from pathlib import Path


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
        proxies (dict[str, str]): Dictionary of proxies to route the request
        auth (Union[dict, AuthSchema]): The authentication information
    """

    endpoint: str = "https://0.0.0.0:8080"
    auth: AuthSchema = dataclasses.field(default_factory=AuthSchema)

    proxies: dict[str, str] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        """Post initialization method to normalize values"""
        # Auth may be present in the config.toml. If it is not, we odn't do
        # anything and go with defaults.
        if isinstance(self.auth, dict):
            self.auth = AuthSchema(**self.auth)
