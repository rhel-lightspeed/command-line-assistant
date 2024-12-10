import shutil

from command_line_assistant.rendering.decorators.base import RenderDecorator


class TextRenderer:
    def __init__(self) -> None:
        # Fetch the current terminal size on initialization
        self.terminal_width = shutil.get_terminal_size().columns
        self._decorators: dict[type, RenderDecorator] = {}

    def update(self, decorator: RenderDecorator) -> None:
        """Update or add a decorator of the same type."""
        self._decorators[type(decorator)] = decorator

    def render(self, text: str):
        decorated_text = text
        # Apply all decorators except Spinner
        for decorator in self._decorators.values():
            decorated_text = decorator.decorate(decorated_text)

        print(decorated_text)
