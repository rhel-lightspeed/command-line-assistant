"""
ANSI color and style utilities.
"""

import os
from enum import Enum


class Color(Enum):
    NORMAL = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    def __str__(self) -> str:
        return self.value


class Style(Enum):
    NORMAL = "\033[0m"
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    STRIKETHROUGH = "\033[9m"

    def __str__(self) -> str:
        return self.value


def colorize(text: str, color: Color) -> str:
    """Colorize text with the specified color."""
    if os.getenv("NO_COLOR"):
        return text
    return f"{color}{text}{Color.NORMAL}"


def stylize(text: str, style: Style) -> str:
    """Format text with the specified style."""
    if os.getenv("NO_COLOR"):
        return text
    return f"{style}{text}{Style.NORMAL}"
