"""Interactive renderer module to handle chat interactive session."""

from typing import Optional

from command_line_assistant.exceptions import StopInteractiveMode
from command_line_assistant.rendering.base import BaseRenderer, BaseStream
from command_line_assistant.rendering.stream import StdoutStream


class InteractiveRenderer(BaseRenderer):
    """This is a specialized class to render output based on the `stream` parameter to the terminal.

    Example:
        This class can be used as this:
            >>> interactive_renderer = InteractiveRenderer()
            >>> interactive_renderer.render(">>> ")
            >>> # Will open an interactive loop waiting for user input
    """

    def __init__(self, banner: str, stream: Optional[BaseStream] = None) -> None:
        """Constructor for the class

        Arguments:
            banner (str): The banner that will greet the user when the
            interactive mode starts.
            stream (Optional[OutputStreamWritter], optional): The stream to
            where the output will be. Can be either `py:StdoutStream` or
            `py:StderrStream`. Defaults to StdoutStream().
        """
        self._banner = banner
        self._output: str = ""
        self._first_message = False
        super().__init__(stream or StdoutStream())

    def render(self, text: str) -> None:
        """The main function to render thext.

        Note:
            The text argument here will be used as a prompt.

        Arguments:
            text (str): The textual value that will be represented in the terminal.

        Raises:
            StopInteractiveMode: In case the interactive mode should be stopped, we will raise this.
        """
        if not self._first_message:
            self._stream.write(self._banner)
            self._stream.write("The current session does not include running context.")
            self._first_message = True

        user_input = input(text).strip()

        # More commands can be added in the future, but for now, we only have .exit
        if user_input == ".exit":
            raise StopInteractiveMode

        self.output = user_input

    @property
    def output(self) -> str:
        """Property to get the value of the internal output

        Returns:
            str: The value of the output stored
        """
        return self._output

    @output.setter
    def output(self, value: str) -> None:
        """Set the value to the output internal property

        Arguments:
            value (str): The value to be set
        """
        self._output = value
