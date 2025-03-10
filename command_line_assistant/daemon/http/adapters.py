"""Main module to track the adapters for the http backend."""

import logging
from typing import Union

from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)


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

        Arguments:
            pool_connections (int, optional): The total amount of pool connections. Defaults to 10.
            pool_maxsize (int, optional): The max size of the pool. Defaults to 10.
            max_retries (Union[Retry, int, None], optional): The maximum number of retires. Defaults to 3.
            pool_block (bool, optional): If the pool should be blocked. Defaults to False.
        """
        logger.info("Configuring retry adapter with max_retries of %s", max_retries)
        retries = Retry(
            total=max_retries,
            backoff_factor=0.1,
            status_forcelist=[502, 503, 504],
            allowed_methods={"POST"},
        )
        super().__init__(pool_connections, pool_maxsize, retries, pool_block)
