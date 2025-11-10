import itertools
import sys
import threading
import time
from typing import Optional


class Spinner:
    """
    A spinner animation that displays a loading indicator and optional message.
    """

    def __init__(self, message: str, plain: bool = False):
        self._message = message
        self._frames = itertools.cycle(
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
        self._spinning = False
        self._stop_event: Optional[threading.Event] = None
        self._current_line_length = 0
        self._plain = plain

    def _animate(self):
        """Animation loop that updates the progress indicator with interrupt
        handling."""
        if self._plain:
            sys.stderr.write(f"{next(self._frames)} {self._message}...")
            sys.stderr.flush()
            return

        while self._stop_event and not self._stop_event.is_set():
            frame = next(self._frames)
            # Clear the current line and write the new frame
            clear_line = "\r" + " " * self._current_line_length + "\r"
            animated_message = f"{frame} {self._message}..."
            self._current_line_length = len(animated_message)

            # Write directly to stderr for real-time animation
            sys.stderr.write(clear_line + animated_message)
            sys.stderr.flush()
            time.sleep(0.1)

    def __enter__(self) -> "Spinner":
        if not self._spinning:
            self._stop_event = threading.Event()
            self._animation_thread = threading.Thread(target=self._animate)
            self._animation_thread.start()
            self._spinning = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._spinning:
            # Stop the animation
            if self._stop_event:
                self._stop_event.set()
            if self._animation_thread:
                self._animation_thread.join()
            self._spinning = False

            sys.stderr.write("\n")
            sys.stderr.flush()
