"""Module to track all *text* decorations applied to renderers"""

import logging
import shutil
import textwrap
from typing import Optional, Union

from command_line_assistant.rendering.base import BaseDecorator

logger = logging.getLogger(__name__)


class EmojiDecorator(BaseDecorator):
    """Decorator class to add emoji to the textual string on the left side of it.

    Example:
        This is an example on how to use this decorator:

        >>> # "U+1F916" is the :robot: emoji. Ref: https://www.compart.com/en/unicode/U+1F916
        >>> decorator = EmojiDecorator("U+1F916")
        >>> renderer.update(decorator)
    """

    def __init__(self, emoji: Union[str, int]) -> None:
        """Constructor of the class.

        Arguments:
            emoji (Union[str, int]): The emoji in either the unicode or hex value.
        """
        self._emoji = self._normalize_emoji(emoji)

    def _normalize_emoji(self, emoji: Union[str, int]) -> str:
        """Internal function to normalize the emoji from either hex or unicode.

        Arguments:
            emoji (Union[str, int]): The emoji in either the unicode or hex value.

        Raises:
            TypeError: In case the emoji provided is not a string or int.

        Returns:
            str: The normalized emoji value, transformed to int (base 16) and then char.
        """
        if isinstance(emoji, int):
            return chr(emoji)

        if isinstance(emoji, str):
            # If already an emoji character
            if len(emoji) <= 2 and ord(emoji[0]) > 127:
                return emoji

            # Convert code point to emoji
            code = emoji.upper().replace("U+", "").replace("0X", "")
            return chr(int(code, 16))

        raise TypeError(f"Emoji must be string or int, not {type(emoji)}")

    def decorate(self, text: str) -> str:
        """Decorate the text string and returns it.

        Arguments:
            text (str): The text that needs to be decorated. This usually is being set from a renderer class.

        Returns:
            str: The text decorated with the emoji.
        """
        return f"{self._emoji} {text}"


class TextWrapDecorator(BaseDecorator):
    """Decorator class to wrap the text to the terminal size.

    Example:
        This is an example on how to use this decorator:

        >>> # Very long message and a terminal width of just 50
        >>> message = "Very long message that will be wrapped for a terminal width of just 50"
        >>> decorator = TextWrapDecorator(width=50)
        >>> renderer.update(decorator)
        >>>
        >>> renderer.render(message)
        >>> # Example of how the message is being printed to the stdout.
        >>> Very long message that will be
        >>> wrapped for a terminal width of
        >>> just 50
    """

    def __init__(self, width: Optional[int] = None, indent: str = "") -> None:
        """Constructor of the class

        Arguments:
            width (Optional[int], optional): The width of the terminal. Defaults to `shutil.get_terminal_size().columns`.
            indent (str, optional): Indentation mode for the string. Defaults to "".
        """
        self._width = width or shutil.get_terminal_size().columns
        self._indent = indent

    def decorate(self, text: str) -> str:
        """Decorate the text string and returns it.

        Arguments:
            text (str): The text that needs to be decorated. This usually is being set from a renderer class.

        Returns:
            str: The text itself wrapped based on the `self._width` and `self._indent` values.
        """
        return textwrap.fill(
            text,
            width=self._width,
            initial_indent=self._indent,
            subsequent_indent=self._indent,
        )
