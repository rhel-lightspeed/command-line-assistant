from unittest.mock import MagicMock

from command_line_assistant.rendering.base import BaseStream


class MockStream(BaseStream):
    """Mock stream class for testing"""

    def __init__(self):
        self.written = []
        super().__init__(stream=MagicMock())

    def write(self, text: str) -> None:
        self.written.append(text)

    def flush(self) -> None:
        pass
