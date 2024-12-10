import shutil
import textwrap
from typing import Optional, Union

from command_line_assistant.rendering.decorators.base import RenderDecorator


class EmojiDecorator(RenderDecorator):
    def __init__(self, emoji: Union[str, int]) -> None:
        self._emoji = self._normalize_emoji(emoji)

    def _normalize_emoji(self, emoji: Union[str, int]) -> str:
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
        return f"{self._emoji} {text}"


class TextWrapDecorator(RenderDecorator):
    def __init__(self, width: Optional[int] = None, indent: str = "") -> None:
        self._width = width or shutil.get_terminal_size().columns
        self._indent = indent

    def decorate(self, text: str) -> str:
        return textwrap.fill(
            text,
            width=self._width,
            initial_indent=self._indent,
            subsequent_indent=self._indent,
        )
