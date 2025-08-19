import itertools
import signal
import sys
import threading
import time
from typing import Optional


class Spinner:
    """
    A spinner animation that displays a loading indicator and optional message.
    """

    def __init__(self, message: str):
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

    def _signal_handler(self, sig, frame):
        if self._stop_event:
            self._stop_event.set()
        raise KeyboardInterrupt

    def _animate(self):
        """Animation loop that updates the progress indicator with interrupt
        handling."""
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
            self._original_handler = signal.signal(signal.SIGINT, self._signal_handler)
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
            signal.signal(signal.SIGINT, self._original_handler)
            self._spinning = False

            # Clear the animation line and add a newline
            if self._current_line_length > 0:
                clear_line = "\r" + " " * self._current_line_length + "\r"
                sys.stderr.write(clear_line)
                sys.stderr.flush()
