"""
The text submodule for rendering deals with how to present text to the terminal.
"""

from typing import Optional

from command_line_assistant.rendering.base import BaseRenderer, BaseStream
from command_line_assistant.rendering.stream import StdoutStream


class TextRenderer(BaseRenderer):
    """This is a specialized class to render output based on the `stream` parameter to the terminal."""

    def __init__(self, stream: Optional[BaseStream] = None) -> None:
        """Constructor of the class

        Example:
            This class can be used as this:
                >>> text_renderer = TextRenderer()
                >>> text_renderer.render("Hello, world!")

        Args:
            stream (Optional[OutputStreamWritter], optional): The stream to where the output will be. Can be either `py:StdoutStream` or `py:StderrStream`. Defaults to StdoutStream().
        """
        super().__init__(stream or StdoutStream())

    def render(self, text: str) -> None:
        """The main function to render thext.

        Args:
            text (str): The textual value that will be represented in the terminal.
        """
        lines = text.splitlines()
        for line in lines:
            decorated_text = self._apply_decorators(line)
            self._stream.execute(decorated_text)
