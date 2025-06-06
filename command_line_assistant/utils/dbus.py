"""Utility class providing common functionality for commands."""

from typing import Optional, cast

from command_line_assistant.dbus.constants import (
    CHAT_IDENTIFIER,
    HISTORY_IDENTIFIER,
    USER_IDENTIFIER,
)
from command_line_assistant.dbus.interfaces.chat import ChatInterface
from command_line_assistant.dbus.interfaces.history import HistoryInterface
from command_line_assistant.dbus.interfaces.user import UserInterface


class DbusUtils:
    """Utility class providing common functionality for commands."""

    def __init__(self) -> None:
        """Initialize command utilities."""
        self._chat_proxy: Optional[ChatInterface] = None
        self._history_proxy: Optional[HistoryInterface] = None
        self._user_proxy: Optional[UserInterface] = None

    @property
    def chat_proxy(self) -> ChatInterface:
        """Get chat proxy instance."""
        if self._chat_proxy is None:
            self._chat_proxy = cast(ChatInterface, CHAT_IDENTIFIER.get_proxy())
        return self._chat_proxy

    @property
    def history_proxy(self) -> HistoryInterface:
        """Get history proxy instance."""
        if self._history_proxy is None:
            self._history_proxy = cast(HistoryInterface, HISTORY_IDENTIFIER.get_proxy())
        return self._history_proxy

    @property
    def user_proxy(self) -> UserInterface:
        """Get user proxy instance."""
        if self._user_proxy is None:
            self._user_proxy = cast(UserInterface, USER_IDENTIFIER.get_proxy())
        return self._user_proxy
