"""
ANSI color and style utilities.
"""

import os
from enum import Enum
from typing import Union


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

    @classmethod
    def from_string(cls, color: Union[str, "Color"]) -> "Color":
        """Create a Color enum value from a named string.

        Args:
            color (str): The name of the color.

        Returns:
            Color: The Color enum value.
        """
        if isinstance(color, Color):
            return color

        _colors = {
            "normal": cls.NORMAL,
            "black": cls.BLACK,
            "red": cls.RED,
            "green": cls.GREEN,
            "yellow": cls.YELLOW,
            "blue": cls.BLUE,
            "magenta": cls.MAGENTA,
            "cyan": cls.CYAN,
            "white": cls.WHITE,
            "bright_black": cls.BRIGHT_BLACK,
            "bright_red": cls.BRIGHT_RED,
            "bright_green": cls.BRIGHT_GREEN,
            "bright_yellow": cls.BRIGHT_YELLOW,
            "bright_blue": cls.BRIGHT_BLUE,
            "bright_magenta": cls.BRIGHT_MAGENTA,
            "bright_cyan": cls.BRIGHT_CYAN,
            "bright_white": cls.BRIGHT_WHITE,
        }
        return _colors[color.lower()] or cls.NORMAL

    def __str__(self) -> str:
        return self.value


class Style(Enum):
    NORMAL = "\033[0m"
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    STRIKETHROUGH = "\033[9m"

    @classmethod
    def from_string(cls, style: Union[str, "Style"]) -> "Style":
        """Create a Style enum value from a named string."""
        if isinstance(style, Style):
            return style

        _styles = {
            "normal": cls.NORMAL,
            "bold": cls.BOLD,
            "italic": cls.ITALIC,
            "underline": cls.UNDERLINE,
            "strikethrough": cls.STRIKETHROUGH,
        }
        return _styles[style.lower()] or cls.NORMAL

    def __str__(self) -> str:
        return self.value


def colorize(text: str, color: Union[Color, str]) -> str:
    """Colorize text with the specified color."""
    if os.getenv("NO_COLOR"):
        return text

    if isinstance(color, Color):
        return f"{color.value}{text}{Color.NORMAL.value}"
    else:
        return f"{Color[color.upper()].value}{text}{Color.NORMAL.value}"


def stylize(text: str, style: Union[Style, str]) -> str:
    """Format text with the specified style."""
    if os.getenv("NO_COLOR"):
        return text
    if isinstance(style, Style):
        return f"{style.value}{text}{Style.NORMAL.value}"
    else:
        return f"{Style[style.upper()].value}{text}{Style.NORMAL.value}"
