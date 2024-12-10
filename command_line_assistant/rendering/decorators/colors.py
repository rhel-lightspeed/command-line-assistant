import os
from typing import Optional

from colorama import Back, Fore, Style

from command_line_assistant.rendering.decorators.base import RenderDecorator


class ColorDecorator(RenderDecorator):
    """Decorator for adding foreground and background colors to text using colorama"""

    # Color name mappings for better IDE support and type checking
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
        """
        Initialize the color decorator with the specified colors and style.

        Args:
            foreground: Foreground color name (default: "white")
            background: Optional background color name
            style: Optional style name ("dim", "normal", "bright")
        """
        self.foreground = self._get_foreground_color(foreground)
        self.background = self._get_background_color(background) if background else ""

    def _get_foreground_color(self, color: str) -> str:
        """Get the colorama foreground color code."""
        color = color.lower()
        if color not in self.FOREGROUND_COLORS:
            raise ValueError(
                f"Invalid foreground color. Choose from: {', '.join(self.FOREGROUND_COLORS.keys())}"
            )
        return self.FOREGROUND_COLORS[color]

    def _get_background_color(self, color: str) -> str:
        """Get the colorama background color code."""
        color = color.lower()
        if color not in self.BACKGROUND_COLORS:
            raise ValueError(
                f"Invalid background color. Choose from: {', '.join(self.BACKGROUND_COLORS.keys())}"
            )
        return self.BACKGROUND_COLORS[color]

    def decorate(self, text: str) -> str:
        """Apply the color formatting to the text."""
        formatted_text = f"{self.background}{self.foreground}{text}{Style.RESET_ALL}"
        return formatted_text


def should_disable_color_output():
    """
    Return whether NO_COLOR exists in environment parameter and is true.

    See https://no-color.org/
    """
    if "NO_COLOR" in os.environ:
        no_color = os.environ["NO_COLOR"]
        return no_color is not None and no_color != "0" and no_color.lower() != "false"

    return False
