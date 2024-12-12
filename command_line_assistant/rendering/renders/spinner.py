import itertools
import threading
import time
from dataclasses import dataclass
from typing import Iterator, Optional

from command_line_assistant.rendering.base import BaseRenderer, OutputStreamWritter
from command_line_assistant.rendering.stream import StdoutStream


@dataclass
class Frames:
    default: Iterator[str] = itertools.cycle(["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"])
    dash: Iterator[str] = itertools.cycle(["-", "\\", "|", "/"])
    circular: Iterator[str] = itertools.cycle(["◐", "◓", "◑", "◒"])
    dots: Iterator[str] = itertools.cycle([".  ", ".. ", "...", " ..", "  .", "   "])
    arrows: Iterator[str] = itertools.cycle(["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"])
    moving: Iterator[str] = itertools.cycle(
        ["[   ]", "[=  ]", "[== ]", "[===]", "[ ==]", "[  =]", "[   ]"]
    )


class SpinnerRenderer(BaseRenderer):
    def __init__(
        self,
        message: str,
        stream: Optional[OutputStreamWritter] = None,
        frames: Iterator[str] = Frames.default,
        delay: float = 0.1,
        clear_message: bool = False,
    ) -> None:
        super().__init__(stream or StdoutStream())
        self._message = message
        self._frames = frames
        self._delay = delay
        self._clear_message = clear_message
        self._done = threading.Event()
        self._spinner_thread: Optional[threading.Thread] = None

    def render(self, text: str) -> None:
        """Render text with all decorators applied."""
        decorated_text = self._apply_decorators(text)
        self._stream.execute(decorated_text)

    def _animation(self) -> None:
        while not self._done.is_set():
            frame = next(self._frames)
            message = self._apply_decorators(f"{frame} {self._message}")
            self._stream.execute(f"\r{message}")
            time.sleep(self._delay)

    def start(self) -> None:
        """Start the spinner animation"""
        self._done.clear()
        self._spinner_thread = threading.Thread(target=self._animation)
        self._spinner_thread.start()

    def stop(self) -> None:
        """Stop the spinner animation"""
        if self._spinner_thread:
            self._done.set()
            self._spinner_thread.join()
            self._stream.execute("\n")
            if self._clear_message:
                self._stream.execute(f"\r{' ' * (len(self._message) + 2)}\r")

    def __enter__(self) -> "SpinnerRenderer":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
