from typing import Optional

from colorama import Style

from command_line_assistant.rendering.decorators.base import RenderDecorator


class StyleDecorator(RenderDecorator):
    """Decorator for adding text styles using colorama"""

    STYLES = {
        "dim": Style.DIM,
        "normal": Style.NORMAL,
        "bright": Style.BRIGHT,
        "reset": Style.RESET_ALL,
    }

    def __init__(self, style: Optional[str] = None) -> None:
        """
        Initialize the style decorator with the specified styles.

        Args:
            style: Name of a style to be applied ("dim", "normal", "bright")
        """
        self.style = self._get_style(style) if style else None

    def _get_style(self, style: str) -> str:
        """Get the colorama style code."""
        style = style.lower()
        if style not in self.STYLES:
            raise ValueError(
                f"Invalid style. Choose from: {', '.join(self.STYLES.keys())}"
            )
        return self.STYLES[style]

    def decorate(self, text: str) -> str:
        """Apply the style formatting to the text."""
        if self.style:
            return f"{self.style}{text}{Style.RESET_ALL}"

        return text
