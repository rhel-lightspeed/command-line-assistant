from typing import List, Optional, Tuple

from command_line_assistant.rendering.base import BaseRenderer, OutputStreamWritter
from command_line_assistant.rendering.stream import StdoutStream


class MenuRenderer(BaseRenderer):
    def __init__(
        self,
        options: List[Tuple[str, str]],
        prompt: str = "Please select an option: ",
        stream: Optional[OutputStreamWritter] = None,
    ) -> None:
        """Initialize menu renderer.

        Args:
            options: List of tuples containing (option_key, option_description)
            prompt: Prompt text to display
            stream: Output stream to use
        """
        super().__init__(stream or StdoutStream())
        self._options = options
        self._prompt = prompt

    def render(self, text: str = "") -> None:
        """Render the menu and get user selection."""
        # Display any context text first
        if text:
            decorated_text = self._apply_decorators(text)
            self._stream.execute(decorated_text)
            self._stream.execute("")  # Empty line after context

        # Display menu options
        for idx, (key, description) in enumerate(self._options, 1):
            menu_item = f"{idx}. {description} [{key}]"
            decorated_item = self._apply_decorators(menu_item)
            self._stream.execute(decorated_item)

        # Display prompt
        self._stream.execute("")  # Empty line before prompt
        prompt_text = self._apply_decorators(self._prompt)
        self._stream.execute(prompt_text)

    def get_selection(self) -> str:
        """Get and validate user selection.

        Returns:
            The key of the selected option
        """
        while True:
            try:
                choice = input().strip()
                # Check if input matches any option key
                for key, _ in self._options:
                    if choice.lower() == key.lower():
                        return key
                # Check if input is a valid number
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(self._options):
                    return self._options[choice_idx - 1][0]
                raise ValueError()
            except (ValueError, IndexError):
                self._stream.execute("Invalid selection. Please try again: ")
