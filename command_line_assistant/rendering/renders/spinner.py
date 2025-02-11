"""
The spinner submodule for rendering shows a spinning text to the terminal.
Used for long running tasks.
"""

import itertools
import locale
import threading
import time
from dataclasses import dataclass
from typing import Iterator, Optional

from command_line_assistant.rendering.base import BaseRenderer, BaseStream
from command_line_assistant.rendering.stream import StdoutStream


@dataclass
class Animation:
    """Dataclass to hold all possible values for spinner frames.

    Attributes:
        frames (Iterator[str]): The frames chosen
        encoding (str): The default encoding.
    """

    frames: Iterator[str]
    encoding: str = "utf8"


#: Constant containing the various configured spinners
#:
#: Elements::
#:      default (Iterator[str]): The default spinner frame (star)
#:      braille (Iterator[str]): A spinner made for braille (⠋)
#:      dash (Iterator[str]): A spinner made with dashes (-)
#:      circular (Iterator[str]): A spinner made with half-circles (◐)
#:      dots (Iterator[str]): A spinner made with dots (.)
#:      arrows (Iterator[str]): A spinner made with an arrow (←)
#:      moving (Iterator[str]): A spinner made with equals signs ([=])
ANIMATIONS = {
    "default": Animation(
        itertools.cycle(
            [
                "⁺₊+",
                "⁻₊+",
                "⁺₊+",
                "⁺₊+",
                "⁺₋+",
                "⁺₊+",
                "⁺₊+",
                "⁺₊−",
                "⁺₊+",
            ]
        )
    ),
    "braille": Animation(itertools.cycle(["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"])),
    "dash": Animation(itertools.cycle(["-", "\\", "|", "/"]), "ascii"),
    "circular": Animation(itertools.cycle(["◐", "◓", "◑", "◒"])),
    "dots": Animation(
        itertools.cycle([".  ", ".. ", "...", " ..", "  .", "   "]), "ascii"
    ),
    "arrows": Animation(itertools.cycle(["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"])),
    "moving": Animation(
        itertools.cycle(
            ["[   ]", "[=  ]", "[== ]", "[===]", "[ ==]", "[  =]", "[   ]"]
        ),
        "ascii",
    ),
}


class SpinnerRenderer(BaseRenderer):
    """This is a specialized class to render output based on the `stream` parameter to the terminal.

    Example:
        This class can be used like this:
            >>> spinner_renderer = SpinnerRenderer()
            >>> with spinner_renderer:
            >>>     # your long running task

        You can pass a custom message for the spinner:
            >>> spinner_renderer = SpinnerRenderer(message="I'm waiting for my cake to finish")
            >>> with spinner_renderer:
            >>>     # your long running task

        Or you can make each frame take longer to process:
            >>> # The default delay is 0.1
            >>> spinner_renderer = SpinnerRenderer(delay=5.0)
            >>> with spinner_renderer:
            >>>     # your long running task
    """

    def __init__(
        self,
        message: str,
        stream: Optional[BaseStream] = None,
        frames: Animation = ANIMATIONS["default"],
        delay: float = 0.1,
        clear_message: bool = False,
    ) -> None:
        """Constructor of the class

        Arguments:
            message (str): The static message that will be shown in every frame
            stream (Optional[OutputStreamWritter], optional): The stream to where the output will be. Can be either `py:StdoutStream` or `py:StderrStream`. Defaults to StdoutStream().
            frames (Iterator[str], optional): A Frame object that will be updated every second. Defaults to ANIMATIONS["default"] in utf-8 capable locales and ANIMATIONS["dash"] otherwise.
            delay (float, optional): Interval of time between each frame. Defaults to 0.1.
            clear_message (bool, optional): If we should clear the message after the long running task finishes. Defaults to False.
        """
        self._message = message
        self._delay = delay
        self._clear_message = clear_message

        # Normalize the frame encoding identifier
        frames_encoding = frames.encoding.lower()
        if frames_encoding.startswith("utf"):
            frames_encoding = frames_encoding.replace("-", "")

        # Only use spinners with characters compatible with the user's locale encoding.
        if frames.encoding != "ascii":
            locale_encoding = locale.getpreferredencoding().lower()
            if locale_encoding.startswith("utf"):
                locale_encoding = locale_encoding.replace("-", "")

            # In non-utf encodings, set frames to an animation that only
            # consists of ASCII characters to prevent sending bytes to the
            # terminal that don't make sense.
            if frames_encoding != locale_encoding:
                frames = ANIMATIONS["dash"]

        self._frames = frames.frames

        self._done = threading.Event()
        self._spinner_thread: Optional[threading.Thread] = None
        super().__init__(stream or StdoutStream())

    def render(self, text: str) -> None:
        """The main function to render the text.

        Note:
            You should not use this method. Instead, check the class examples.

        Arguments:
            text (str): The textual value that will be represented in the terminal.

        Raises:
            NotImplementedError: The render function is not implemneted for this class. The main idea is to use it as a contextmanager.
        """
        raise NotImplementedError(
            "Render function is not implemented for SpinnerRenderer class."
        )

    def _animation(self) -> None:
        """Internal method to control the text being rendered.

        This differs from the main `py:render` implementation as we want to use
        the `py:SpinnerRenderer` as a contextmanager.

        This applies the decorators of a text on each frame to keep
        consistency. It uses a thread to validate if we should still output
        text to the screen or not.
        """
        while not self._done.is_set():
            frame = next(self._frames)
            message = self._apply_decorators(f"{frame} {self._message}")
            self._stream.execute(f"\r{message}")
            time.sleep(self._delay)

    def start(self) -> None:
        """Start the spinner animation.

        Starts the thread that will handle the animatoin of the screen.
        """
        self._done.clear()
        self._spinner_thread = threading.Thread(target=self._animation)
        self._spinner_thread.start()

    def stop(self) -> None:
        """Stop the spinner animation.

        Stop the thread that handles the animation of the screen.
        """
        if self._spinner_thread:
            self._done.set()
            self._spinner_thread.join()
            self._stream.execute("\n")
            if self._clear_message:
                self._stream.execute(f"\r{' ' * (len(self._message) + 2)}\r")

    def __enter__(self) -> "SpinnerRenderer":
        """The special contextmanager method to start the spinner.

        Returns:
            SpinnerRenderer: Return itself.
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """The special contextmanager method to stop the spinner."""
        self.stop()
