import itertools
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator, Iterator


@dataclass
class Frames:
    default: Iterator[str] = itertools.cycle(["-", "\\", "|", "/"])
    braille: Iterator[str] = itertools.cycle(["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"])
    circular: Iterator[str] = itertools.cycle(["◐", "◓", "◑", "◒"])
    dots: Iterator[str] = itertools.cycle([".  ", ".. ", "...", " ..", "  .", "   "])
    arrows: Iterator[str] = itertools.cycle(["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"])
    moving: Iterator[str] = itertools.cycle(
        ["[   ]", "[=  ]", "[== ]", "[===]", "[ ==]", "[  =]", "[   ]"]
    )


@contextmanager
def ascii_spinner(
    message: str,
    clear_message: bool = False,
    frames: Iterator[str] = Frames.default,
    delay: float = 0.1,
) -> Generator:
    done = threading.Event()

    def animation() -> None:
        while not done.is_set():
            sys.stdout.write(f"\r{next(frames)} {message}")  # Write the current frame
            sys.stdout.flush()
            time.sleep(delay)  # Delay between frames

    spinner_thread = threading.Thread(target=animation)
    spinner_thread.start()

    try:
        yield
    finally:
        done.set()  # Signal the spinner to stop
        spinner_thread.join()  # Wait for the spinner thread to finish
        sys.stdout.write("\r\n")
        if clear_message:
            # Clear the message by overwriting it with spaces and resetting the cursor
            sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")  # Clear the line
            sys.stdout.flush()
