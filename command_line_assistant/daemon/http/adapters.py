"""Main module to track the adapters for the http backend."""

import ssl
from pathlib import Path
from typing import Union

from requests.adapters import HTTPAdapter
from urllib3 import Retry


class SSLAdapter(HTTPAdapter):
    """Create an adapter to use a custom SSL context in requests.

    Attributes:
        cert_file (Path): The path to the cert file on the system
        key_file (Path): The path to the key file on the system
        ssl_context: Any additional ssl context that needs to be used
    """

    def __init__(self, cert_file: Path, key_file: Path, ssl_context=None, **kwargs):
        """Constructor of the class

        Args:
            cert_file (Path): The path to the cert file on the system
            key_file (Path): The path to the key file on the system
            ssl_context: Any additional ssl context that needs to be used. Defaults to None.
        """
        self.cert_file = cert_file
        self.key_file = key_file
        self.ssl_context = ssl_context or ssl.create_default_context()
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs) -> None:
        """Initialize the poolmanager"""
        # Load the certificate and key into the SSL context
        self.ssl_context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
        kwargs["ssl_context"] = self.ssl_context
        super().init_poolmanager(*args, **kwargs)


class RetryAdapter(HTTPAdapter):
    """Create an adapter to use custom retry."""

    def __init__(
        self,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        max_retries: Union[int, None] = 3,
        pool_block: bool = False,
    ) -> None:
        """Constructor of the class.

        Args:
            pool_connections (int, optional): The total amount of pool connections. Defaults to 10.
            pool_maxsize (int, optional): The max size of the pool. Defaults to 10.
            max_retries (Union[Retry, int, None], optional): The maximum number of retires. Defaults to 3.
            pool_block (bool, optional): If the pool should be blocked. Defaults to False.
        """
        retries = Retry(
            total=max_retries,
            backoff_factor=0.1,
            status_forcelist=[502, 503, 504],
            allowed_methods={"POST"},
        )
        super().__init__(pool_connections, pool_maxsize, retries, pool_block)
