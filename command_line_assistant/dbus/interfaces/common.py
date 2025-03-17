"""D-Bus interfaces that defines and powers our commands."""

import logging

from dasbus.typing import Bool

logger = logging.getLogger(__name__)


class CommonInterface:
    """The DBus interface of a query."""

    def IsAllowed(self) -> Bool:
        """Get all the chat session for a given user.

        Arguments:
            user_id (Str): The identifier of the user.

        Returns:
            Structure: The list of chat sessions.
        """
        return True
