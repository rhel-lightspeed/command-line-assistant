import shutil
from typing import Optional

from command_line_assistant.rendering.base import BaseRenderer, OutputStreamWritter
from command_line_assistant.rendering.stream import StdoutStream


class TextRenderer(BaseRenderer):
    def __init__(self, stream: Optional[OutputStreamWritter] = None) -> None:
        super().__init__(stream or StdoutStream())
        self.terminal_width = shutil.get_terminal_size().columns

    def render(self, text: str) -> None:
        """Render text with all decorators applied."""
        lines = text.splitlines()
        for line in lines:
            decorated_text = self._apply_decorators(line)
            self._stream.execute(decorated_text)
