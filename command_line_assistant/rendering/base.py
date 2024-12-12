from abc import ABC, abstractmethod
from typing import TextIO


class RenderDecorator(ABC):
    """Abstract base class for render decorators"""

    @abstractmethod
    def decorate(self, text: str) -> str:
        pass


class OutputStreamWritter(ABC):
    """Abstract base class for output stream decorators"""

    def __init__(self, stream: TextIO, end: str = "\n") -> None:
        """
        Initialize the output stream decorator.

        Args:
            stream: The output stream to use
            end: The string to append after the text (defaults to newline)
        """
        self._stream = stream
        self._end = end

    @abstractmethod
    def write(self, text: str) -> None:
        """Write the text to the output stream"""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush the output stream"""
        pass

    def execute(self, text: str) -> None:
        """
        Write the text to the output stream and return the original text for chaining.
        """
        if text:
            self.write(text)
            self.flush()


class BaseRenderer(ABC):
    """Base class for renderers providing common functionality."""

    def __init__(self, stream: OutputStreamWritter) -> None:
        self._stream = stream
        self._decorators: dict[type, RenderDecorator] = {}

    def update(self, decorator: RenderDecorator) -> None:
        """Update or add a decorator of the same type."""
        self._decorators[type(decorator)] = decorator

    def _apply_decorators(self, text: str) -> str:
        """Apply all decorators to the text."""
        decorated_text = text
        for decorator in self._decorators.values():
            decorated_text = decorator.decorate(decorated_text)
        return decorated_text

    @abstractmethod
    def render(self, text: str) -> None:
        """Render the text with all decorators applied."""
        pass
