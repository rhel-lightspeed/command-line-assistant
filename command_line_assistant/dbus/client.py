"""Utility module that holds dbus classes."""

from typing import Optional, cast

from command_line_assistant.dbus.constants import (
    CHAT_IDENTIFIER,
    HISTORY_IDENTIFIER,
    USER_IDENTIFIER,
)
from command_line_assistant.dbus.interfaces.chat import ChatInterface
from command_line_assistant.dbus.interfaces.history import HistoryInterface
from command_line_assistant.dbus.interfaces.user import UserInterface


class DbusClient:
    """Utility class providing initialization and access to various bus channels.


    This class exist with the purpose to make all dbus channels available to
    any sub-commands at any given point in time. Since the commands usually
    need to communicate with different channels, and to avoid to re-initialize
    them across the application, this class exists to facilitate the job of the
    sub-commands to have a single interface to call any channel they need.
    """

    def __init__(self) -> None:
        """Initialize command utilities."""
        self._chat_proxy: Optional[ChatInterface] = None
        self._history_proxy: Optional[HistoryInterface] = None
        self._user_proxy: Optional[UserInterface] = None

    @property
    def chat_proxy(self) -> ChatInterface:
        """Get chat proxy instance.

        Returns:
            ChatInterface: An instance of ChatInterface with access to its methods.
        """
        if self._chat_proxy is None:
            self._chat_proxy = cast(ChatInterface, CHAT_IDENTIFIER.get_proxy())
        return self._chat_proxy

    @property
    def history_proxy(self) -> HistoryInterface:
        """Get history proxy instance.

        Returns:
            HistoryInterface: An instance of HistoryInterface with access to its methods.
        """
        if self._history_proxy is None:
            self._history_proxy = cast(HistoryInterface, HISTORY_IDENTIFIER.get_proxy())
        return self._history_proxy

    @property
    def user_proxy(self) -> UserInterface:
        """Get user proxy instance.

        Returns:
            UserInterface: An instance of UserInterface with access to its methods.
        """
        if self._user_proxy is None:
            self._user_proxy = cast(UserInterface, USER_IDENTIFIER.get_proxy())
        return self._user_proxy
