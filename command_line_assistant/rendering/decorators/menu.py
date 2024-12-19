from command_line_assistant.rendering.base import RenderDecorator


class MenuDecorator(RenderDecorator):
    """Decorator for styling menu items"""

    def __init__(self, highlight_keys: bool = True) -> None:
        self._highlight_keys = highlight_keys

    def decorate(self, text: str) -> str:
        if not self._highlight_keys:
            return text

        # Highlight the key portion in brackets
        if "[" in text and "]" in text:
            start = text.rindex("[")
            end = text.rindex("]") + 1
            key_part = text[start:end]
            return f"{text[:start]}\033[1m{key_part}\033[0m"
        return text
