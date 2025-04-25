"""Base class for all interfaces."""

import logging

from dasbus.typing import Bool, Str
logger = logging.getLogger(__name__)


class BaseInterface:
    """Base class for all interfaces."""

    def IsAllowed(self, user_id: Str) -> Bool:
        """Verify if user is allowed to access this bus interface.

        Arguments:
            user_id (Str): The identifier of the user.
        
        Note::
            This is a dummy method that always returns True.
        """
        logger.info(
            "The method IsAllowed was accessed by user '%s' in the parent class '%s'.", user_id, self.__class__.__name__
        )
        return True
