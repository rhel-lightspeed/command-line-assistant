"""
The spinner submodule for rendering show a spinning text to the terminal used
for long running tasks.
"""

import itertools
import threading
import time
from dataclasses import dataclass
from typing import Iterator, Optional

from command_line_assistant.rendering.base import BaseRenderer, BaseStream
from command_line_assistant.rendering.stream import StdoutStream


@dataclass
class Frames:
    """Dataclass to hold all possible values for spinner frames.

    Example::
        This is how each spinner will be represented as 1 character in the
        terminal. Read from left to right.

        >>> default = (["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"]
        >>> dash = ["-", "\\", "|", "/"]
        >>> circular = ["◐", "◓", "◑", "◒"]
        >>> dots = [".  ", ".. ", "...", " ..", "  .", "   "]
        >>> arrows = ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"
        >>> moving = ["[   ]", "[=  ]", "[== ]", "[===]", "[ ==]", "[  =]", "[   ]"]

    Attributes:
        default (Iterator[str]): The default spinner frame (braille)
        dash (Iterator[str]): A spinner made with dashes (-)
        circular (Iterator[str]): A spinner made with half-circles (◐)
        dots (Iterator[str]): A spinner made with dots (.)
        arrows (Iterator[str]): A spinner made with an arrow (←)
        moving (Iterator[str]): A spinner made with equals ([=])
    """

    default: Iterator[str] = itertools.cycle(["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"])
    dash: Iterator[str] = itertools.cycle(["-", "\\", "|", "/"])
    circular: Iterator[str] = itertools.cycle(["◐", "◓", "◑", "◒"])
    dots: Iterator[str] = itertools.cycle([".  ", ".. ", "...", " ..", "  .", "   "])
    arrows: Iterator[str] = itertools.cycle(["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"])
    moving: Iterator[str] = itertools.cycle(
        ["[   ]", "[=  ]", "[== ]", "[===]", "[ ==]", "[  =]", "[   ]"]
    )


class SpinnerRenderer(BaseRenderer):
    """This is a specialized class to render output based on the `stream` parameter to the terminal.

    Example:
        This class can be used as this:
            >>> spinner_renderer = SpinnerRenderer()
            >>> with spinner_renderer:
            >>>     # your long running task

        You can pass a custom message for the spinner:
            >>> spinner_renderer = SpinnerRenderer(message="I'm waiting for my cake to finish")
            >>> with spinner_renderer:
            >>>     # your long running task

        Or you can make each frame to take longer to process:
            >>> # The default delay is 0.1
            >>> spinner_renderer = SpinnerRenderer(delay=5.0)
            >>> with spinner_renderer:
            >>>     # your long running task
    """

    def __init__(
        self,
        message: str,
        stream: Optional[BaseStream] = None,
        frames: Iterator[str] = Frames.default,
        delay: float = 0.1,
        clear_message: bool = False,
    ) -> None:
        """Constructor of the class

        Args:
            message (str): The static message that will be shown in every frame
            stream (Optional[OutputStreamWritter], optional): The stream to where the output will be. Can be either `py:StdoutStream` or `py:StderrStream`. Defaults to StdoutStream().
            frames (Iterator[str], optional): The textual frame that will be updated every second. Defaults to Frames.default.
            delay (float, optional): Interval of time between each frame. Defaults to 0.1.
            clear_message (bool, optional): If we should clear the message after the long running task finishes. Defaults to False.
        """
        self._message = message
        self._frames = frames
        self._delay = delay
        self._clear_message = clear_message
        self._done = threading.Event()
        self._spinner_thread: Optional[threading.Thread] = None
        super().__init__(stream or StdoutStream())

    def render(self, text: str) -> None:
        """The main function to render thext.

        Note:
            You should not use this method. Instead, check the class examples.

        Args:
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
