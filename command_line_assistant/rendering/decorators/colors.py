"""Module to track all *color* decorations applied to renderers"""

import os
from typing import Optional

from colorama import Back, Fore, Style

from command_line_assistant.rendering.base import BaseDecorator


class ColorDecorator(BaseDecorator):
    """Decorator for adding foreground and background colors to text using colorama

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
        "black": Fore.BLACK,
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE,
        "reset": Fore.RESET,
        # Light variants
        "lightblack": Fore.LIGHTBLACK_EX,
        "lightred": Fore.LIGHTRED_EX,
        "lightgreen": Fore.LIGHTGREEN_EX,
        "lightyellow": Fore.LIGHTYELLOW_EX,
        "lightblue": Fore.LIGHTBLUE_EX,
        "lightmagenta": Fore.LIGHTMAGENTA_EX,
        "lightcyan": Fore.LIGHTCYAN_EX,
        "lightwhite": Fore.LIGHTWHITE_EX,
    }

    BACKGROUND_COLORS = {
        "black": Back.BLACK,
        "red": Back.RED,
        "green": Back.GREEN,
        "yellow": Back.YELLOW,
        "blue": Back.BLUE,
        "magenta": Back.MAGENTA,
        "cyan": Back.CYAN,
        "white": Back.WHITE,
        "reset": Back.RESET,
        # Light variants
        "lightblack": Back.LIGHTBLACK_EX,
        "lightred": Back.LIGHTRED_EX,
        "lightgreen": Back.LIGHTGREEN_EX,
        "lightyellow": Back.LIGHTYELLOW_EX,
        "lightblue": Back.LIGHTBLUE_EX,
        "lightmagenta": Back.LIGHTMAGENTA_EX,
        "lightcyan": Back.LIGHTCYAN_EX,
        "lightwhite": Back.LIGHTWHITE_EX,
    }

    def __init__(
        self,
        foreground: str = "white",
        background: Optional[str] = None,
    ) -> None:
        """Constructor of the class.

        Args:
            foreground (str, optional): Foreground color name. Defaults to "white".
            background (Optional[str], optional): Background color name. Defaults to None.
        """
        self.foreground = self._get_foreground_color(foreground)
        self.background = self._get_background_color(background) if background else ""

    def _get_foreground_color(self, color: str) -> str:
        """Get the unicode for the requested color.

        Args:
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
        return self.FOREGROUND_COLORS[color]

    def _get_background_color(self, color: str) -> str:
        """Get the unicode for the requested color.

        Args:
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
        return self.BACKGROUND_COLORS[color]

    def decorate(self, text: str) -> str:
        """Decorate the text string and returns it.

        Args:
            text (str): The text that needs to be decorated. This usually is being set from a renderer class.

        Returns:
            str: The text itself colored with the requested foreground and (optionally) background color.
        """
        formatted_text = f"{self.background}{self.foreground}{text}{Style.RESET_ALL}"
        return formatted_text


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
