import ssl
from typing import Union

from requests.adapters import HTTPAdapter
from urllib3 import Retry


class SSLAdapter(HTTPAdapter):
    """Create an adapter to use a custom SSL context in requests."""

    def __init__(self, cert_file, key_file, ssl_context=None, **kwargs):
        self.cert_file = cert_file
        self.key_file = key_file
        self.ssl_context = ssl_context or ssl.create_default_context()
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        # Load the certificate and key into the SSL context
        self.ssl_context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
        kwargs["ssl_context"] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)


class RetryAdapter(HTTPAdapter):
    """Create an adapter to use custom retry."""

    def __init__(
        self,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        max_retries: Union[Retry, int, None] = 0,
        pool_block: bool = False,
    ) -> None:
        retries = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[502, 503, 504],
            allowed_methods={"POST"},
        )
        super().__init__(pool_connections, pool_maxsize, retries, pool_block)
