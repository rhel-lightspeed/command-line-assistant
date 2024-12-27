"""Module to track all *text* decorations applied to renderers"""

import shutil
import textwrap
from pathlib import Path
from typing import Optional, Union

from command_line_assistant.rendering.base import BaseDecorator
from command_line_assistant.utils.environment import get_xdg_state_path


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

        Args:
            emoji (Union[str, int]): The emoji in either the unicode or hex value.
        """
        self._emoji = self._normalize_emoji(emoji)

    def _normalize_emoji(self, emoji: Union[str, int]) -> str:
        """Internal function to normalize the emoji from either hex or unicode.

        Args:
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

        Args:
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

        Args:
            width (Optional[int], optional): The width of the terminal. Defaults to `shutil.get_terminal_size().columns`.
            indent (str, optional): Indentation mode for the string. Defaults to "".
        """
        self._width = width or shutil.get_terminal_size().columns
        self._indent = indent

    def decorate(self, text: str) -> str:
        """Decorate the text string and returns it.

        Args:
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


class WriteOnceDecorator(BaseDecorator):
    """Decorator that ensures content is written only once by checking a state file.

    The state file is created under $XDG_STATE_HOME/command-line-assistant/<state_filename>

    Example:
        This is an example on how to use this decorator:

        >>> message = "Message that will be printed only once"
        >>> decorator = WriteOnceDecorator(state_filename="legal")
        >>> renderer.update(decorator)
        >>> renderer.render(message)
        >>> renderer.render(message) # This won't show again
    """

    def __init__(self, state_filename: str = "written") -> None:
        """Constructor of the class

        Args:
            state_filename (str): Name of the state file to create/check. Defaults to "written"
        """
        self._state_dir = Path(get_xdg_state_path(), "command-line-assistant")
        self._state_file = self._state_dir / state_filename

    def _should_write(self) -> bool:
        """Check if content should be written by verifying state file existence.

        Returns:
            bool: In Return a boolean value if the state file can be written.
        """
        if self._state_file.exists():
            return False

        if not self._state_dir.exists():
            # Create directory if it doesn't exist
            self._state_dir.mkdir(parents=True)

        # Write state file
        self._state_file.write_text("1")
        return True

    def decorate(self, text: str) -> str:
        """Write the text only if it hasn't been written before.

        Args:
            text (str): The text that needs to be decorated. This usually is being set from a renderer class.

        Returns:
            str: The text decorated if it can writes, otherwise, blank string.
        """
        return text if self._should_write() else ""
