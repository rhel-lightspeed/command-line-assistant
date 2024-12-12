import shutil
import textwrap
from pathlib import Path
from typing import Optional, Union

from command_line_assistant.rendering.base import RenderDecorator
from command_line_assistant.utils.environment import get_xdg_state_path


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


class WriteOnceDecorator(RenderDecorator):
    """Decorator that ensures content is written only once by checking a state file.

    The state file is created under $XDG_STATE_HOME/command-line-assistant/legal/
    """

    def __init__(self, state_filename: str = "written") -> None:
        """Initialize the write once decorator.

        Args:
            state_filename: Name of the state file to create/check
        """
        self._state_dir = Path(get_xdg_state_path(), "command-line-assistant")
        self._state_file = self._state_dir / state_filename

    def _should_write(self) -> bool:
        """Check if content should be written by verifying state file existence."""
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
            text: The text to potentially write

        Returns:
            The text if it should be written, None otherwise
        """
        return text if self._should_write() else ""
