"""Module to track all *color* decorations applied to renderers"""

import os
from typing import Optional

from command_line_assistant.rendering.base import BaseDecorator

RESET_ALL = "\033[0m"


class ColorDecorator(BaseDecorator):
    """Decorator for adding foreground and background colors to text

    Example:
        This is an example on how to use this decorator:

        >>> decorator = ColorDecorator(foreground="magenta")
        >>> renderer.update(decorator)
        >>> renderer.render(message)

        >>> decorator = ColorDecorator(background="red")
        >>> renderer.update(decorator)
        >>> renderer.render(message)

        >>> decorator = ColorDecorator(foreground="magenta", background="red")
        >>> renderer.update(decorator)
        >>> renderer.render(message)

    Attributes:
        FOREGROUND_COLORS (dict[str, str]): The foreground color to be applied to the text. They contain normal and light variants.
        BACKGROUND_COLORS (dict[str, str]): The background color to be applied to the text. They contain normal and light variants.
    """

    FOREGROUND_COLORS = {
        "black": 30,
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
        "magenta": 35,
        "cyan": 36,
        "white": 37,
        "reset": 39,
        # Light variants
        "lightblack": 90,
        "lightred": 91,
        "lightgreen": 92,
        "lightyellow": 93,
        "lightblue": 94,
        "lightmagenta": 95,
        "lightcyan": 96,
        "lightwhite": 96,
    }

    BACKGROUND_COLORS = {
        "black": 40,
        "red": 41,
        "green": 42,
        "yellow": 43,
        "blue": 44,
        "magenta": 45,
        "cyan": 46,
        "white": 47,
        "reset": 49,
        # Light variants
        "lightblack": 100,
        "lightred": 101,
        "lightgreen": 102,
        "lightyellow": 103,
        "lightblue": 104,
        "lightmagenta": 105,
        "lightcyan": 106,
        "lightwhite": 107,
    }

    def __init__(
        self,
        foreground: str = "white",
        background: Optional[str] = None,
    ) -> None:
        """Constructor of the class.

        Arguments:
            foreground (str, optional): Foreground color name. Defaults to "white".
            background (Optional[str], optional): Background color name. Defaults to None.
        """
        self.foreground = self._get_foreground_color(foreground)
        self.background = self._get_background_color(background) if background else ""

    def start(self) -> str:
        """Returns just the starting ANSI sequence without the reset code.

        Returns:
            str: ANSI sequence to start the color formatting
        """
        result = ""
        if should_disable_color_output():
            return result

        if self.background:
            result += self.background
        if self.foreground:
            result += self.foreground
        return result

    def _get_foreground_color(self, color: str) -> str:
        """Get the unicode for the requested color.

        Arguments:
            color (str): Name of the foreground color

        Raises:
            ValueError: In case the requested color is not mapped in the `self.FOREGROUND_COLORS` dictionary.

        Returns:
            str: The unicode of the color requested.
        """
        color = color.lower()
        if color not in self.FOREGROUND_COLORS:
            raise ValueError(
                f"Invalid foreground color. Choose from: {', '.join(self.FOREGROUND_COLORS.keys())}"
            )
        return f"\033[{self.FOREGROUND_COLORS[color]}m"

    def _get_background_color(self, color: str) -> str:
        """Get the unicode for the requested color.

        Arguments:
            color (str): Name of the background color

        Raises:
            ValueError: In case the requested color is not mapped in the `self.BACKGROUND_COLORS` dictionary.

        Returns:
            str: The unicode of the color requested.
        """
        color = color.lower()
        if color not in self.BACKGROUND_COLORS:
            raise ValueError(
                f"Invalid background color. Choose from: {', '.join(self.BACKGROUND_COLORS.keys())}"
            )
        return f"\033[{self.BACKGROUND_COLORS[color]}m"

    def decorate(self, text: str) -> str:
        """Decorate the text string and returns it.

        Arguments:
            text (str): The text that needs to be decorated. This usually is being set from a renderer class.

        Returns:
            str: The text itself colored with the requested foreground and (optionally) background color.
        """
        if not should_disable_color_output():
            return f"{self.start()}{text}{RESET_ALL}"
        return text


def should_disable_color_output() -> bool:
    """
    Return whether NO_COLOR exists in environment parameter and is true.

    See https://no-color.org/

    Returns:
        bool: If color output should be disabled or not.
    """
    if "NO_COLOR" in os.environ:
        no_color = os.environ["NO_COLOR"]
        return no_color is not None and no_color != "0" and no_color.lower() != "false"

    return False
