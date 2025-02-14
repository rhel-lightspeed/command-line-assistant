"""Base module to track all the abstract classes for the rendering module."""

from abc import ABC, abstractmethod
from typing import TextIO


class BaseDecorator(ABC):
    """Abstract base class for render decorators."""

    @abstractmethod
    def decorate(self, text: str) -> str:
        """Decorate the text string and returns it.

        Arguments:
            text (str): The text that needs to be decorated. This usually is
            being set from a renderer class.

        Returns:
            str: The text decorated.
        """


class BaseStream:
    """Abstract base class for output stream decorators"""

    def __init__(self, stream: TextIO, end: str = "\n") -> None:
        """Constructor of the class.

        Arguments:
            stream (TextIO): The stream to use (stdout or stderr).
            end (str, optional): How the line should end in the stream. Defaults to newline.
        """

        self._stream = stream
        self._end = end

    def write(self, text: str) -> None:
        """Write the text to the output stream

        Arguments:
            text (str): The text to be written
        """

        self._stream.write(f"{text}{self._end}")

    def flush(self) -> None:
        """Flush the output stream"""

        self._stream.flush()

    def execute(self, text: str) -> None:
        """
        Write the text to the output stream and flush it immediately.

        Arguments:
            text (str): The text to be written
        """

        if text:
            self.write(text)
            self.flush()


class BaseRenderer(ABC):
    """Base class for renderers providing common functionality."""

    def __init__(self, stream: BaseStream) -> None:
        """Constructor of the class.

        Arguments:
            stream (OutputStreamWritter): The instance of a stream writer (either stdout or stderr).
        """

        self._stream = stream
        self._decorators: dict[type, BaseDecorator] = {}

    def update(self, decorators: list[BaseDecorator]) -> None:
        """Update or add a decorator of the same type.

        Arguments:
            decorator (list[BaseDecorator]): An instance of a rendering
            decorator to be applied.
        """
        if not isinstance(decorators, list):
            raise TypeError(f"decorators must be a list, not '{type(decorators)}'")

        for decorator in decorators:
            self._decorators[type(decorator)] = decorator

    def _apply_decorators(self, text: str) -> str:
        """Apply all decorators to the text.

        Arguments:
            text (str): The text to be apply the decorator customization

        Returns:
            str: The text decorated
        """

        decorated_text = text
        for decorator in self._decorators.values():
            decorated_text = decorator.decorate(decorated_text)
        return decorated_text

    @abstractmethod
    def render(self, text: str) -> None:
        """Render the text with decorators applied.

        It uses the `self._decorators` property to apply the decorators.

        Arguments:
            text (str): The text to be rendered.
        """
