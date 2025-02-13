"""Module to track all *style* decorations applied to renderers"""

from typing import Optional

from command_line_assistant.rendering.base import BaseDecorator

RESET_ALL = "\033[0m"


class StyleDecorator(BaseDecorator):
    """Decorator class to add font style to the textual string.

    Example:
        This is an example on how to use this decorator:

        >>> decorator = StyleDecorator(style="dim")
        >>> renderer.update(decorator)
        >>> renderer.render(message)

    Attributes:
        STYLES: dict[str, str]: A dictionary containing the styles available to the decorator.
    """

    STYLES = {
        "bright": 1,
        "dim": 2,
        "normal": 22,
        "reset": 0,
    }

    def __init__(self, style: Optional[str] = None) -> None:
        """Constructor of the class.

        Arguments:
            style (Optional[str], optional): Name of a style to be applied ("dim", "normal", "bright"). Defaults to None.
        """
        self.style = self._get_style(style) if style else None

    def _get_style(self, style: str) -> str:
        """Get the appropriate style unicode representation.

        Arguments:
            style (str): The name of the style that matches the values in `self.STYLES`

        Raises:
            ValueError: In case the specified style is not present in `self.STYLES` class attribute.

        Returns:
            str: The font style unicode.
        """
        style = style.lower()
        if style not in self.STYLES:
            raise ValueError(
                f"Invalid style. Choose from: {', '.join(self.STYLES.keys())}"
            )
        return f"\033[{self.STYLES[style]}m"

    def decorate(self, text: str) -> str:
        """Decorate the text string and returns it.

        Arguments:
            text (str): The text that needs to be decorated. This usually is being set from a renderer class.

        Returns:
            str: The text decorated with the font style.
        """
        if self.style:
            return f"{self.style}{text}{RESET_ALL}"

        return text
