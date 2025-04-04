"""
The text submodule for rendering deals with how to present text to the terminal.
"""

from typing import Optional

from command_line_assistant.rendering.base import BaseRenderer, BaseStream
from command_line_assistant.rendering.stream import StdoutStream


class TextRenderer(BaseRenderer):
    """Specialized class to render textual output"""

    def __init__(self, stream: Optional[BaseStream] = None) -> None:
        """Constructor of the class

        Example:
            This class can be used as this:

                >>> text_renderer = TextRenderer()
                >>> text_renderer.render("Hello, world!")

        Arguments:
            stream (Optional[BaseStream], optional): The stream to where the output will be. Can be either `py:StdoutStream` or `py:StderrStream`.
        """
        super().__init__(stream or StdoutStream())

    def render(self, text: str) -> None:
        """The main function to render thext.

        Arguments:
            text (str): The textual value that will be represented in the terminal.
        """
        lines = text.splitlines()
        for line in lines:
            decorated_text = self._apply_decorators(line)
            self._stream.execute(decorated_text)


class PlainTextRenderer(TextRenderer):
    """Specialized class to render plain text output without any decorations"""

    def render(self, text: str) -> None:
        """The main function to render the text.

        Arguments:
            text (str): The textual value that will be represented in the terminal.
        """
        lines = text.splitlines()
        for line in lines:
            self._stream.execute(line)
