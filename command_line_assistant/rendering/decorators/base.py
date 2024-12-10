from abc import ABC, abstractmethod


class RenderDecorator(ABC):
    """Abstract base class for render decorators"""

    @abstractmethod
    def decorate(self, text: str) -> str:
        pass
