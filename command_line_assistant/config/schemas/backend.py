"""Schemas for the backend config."""

import dataclasses
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


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

        # TODO(r0x0d): Once we remove the depreaction notice, remove this as well.
        if self.verify_ssl:
            logger.info(
                "Verify SSL option is deprecated and will be removed in the future."
            )
            logger.info("Ignoring Verify SSL option as it has no effect anymore.")


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

        # If the proxies are not set in the config.toml, set the environment variables.
        if not self.proxies:
            http_proxy = os.environ.get("http_proxy")
            if http_proxy:
                self.proxies["http"] = http_proxy

            https_proxy = os.environ.get("https_proxy")
            if https_proxy:
                self.proxies["https"] = https_proxy
