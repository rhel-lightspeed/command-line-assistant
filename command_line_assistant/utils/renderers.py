"""Utility module that provides standarized functions for rendering"""

from typing import Optional

from command_line_assistant.rendering.base import BaseDecorator, BaseStream
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
    TextWrapDecorator,
)
from command_line_assistant.rendering.renders.spinner import SpinnerRenderer
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.rendering.stream import StderrStream, StdoutStream


def create_error_renderer() -> TextRenderer:
    """Create a standarized instance of text rendering for error output

    Returns:
        TextRenderer: Instance of a TextRenderer with correct decorators for
        error output.
    """
    renderer = create_text_renderer(
        [
            EmojiDecorator(emoji="U+1F641"),
            ColorDecorator(foreground="red"),
        ],
        StderrStream(),
    )

    return renderer


def create_warning_renderer() -> TextRenderer:
    """Create a standarized instance of text rendering for error output

    Returns:
        TextRenderer: Instance of a TextRenderer with correct decorators for
        error output.
    """
    renderer = create_text_renderer(
        [
            EmojiDecorator(emoji="0x1f914"),
            ColorDecorator(foreground="yellow"),
        ],
        StderrStream(),
    )

    return renderer


def create_spinner_renderer(
    message: str, decorators: list[BaseDecorator]
) -> SpinnerRenderer:
    """Create a new instance of a spinner renderer.

    Note:
        `py:TextWrapDecorator` is applied automatically to the renderer.

    Args:
        message (str): The message to show while spinning
        decorators (list[BaseDecorator]): List of decorators that can be
        applied to the spinner renderer.

    Returns:
        SpinnerRenderer: Instance of a SpinnerRenderer with decorators applied.
    """
    spinner = SpinnerRenderer(message, stream=StdoutStream(end=""))
    decorators.append(TextWrapDecorator())
    spinner.update(decorators)
    return spinner


def create_text_renderer(
    decorators: Optional[list[BaseDecorator]] = None,
    stream: Optional[BaseStream] = None,
) -> TextRenderer:
    """Create a new instance of a text renderer.

    Note:
        `py:TextWrapDecorator` is applied automatically to the renderer.

    Note:
        If no `stream` is provided in the arguments, it will default to the
        `py:StdoutStream()`.

    Args:
        decorators (Optional[list[BaseDecorator]], optional): List of
        decorators that can be applied to the text renderer. Defaults to None.
        stream (Optional[BaseStream], optional): Apply a different stream other
        than the StdoutStream. Defaults to None.

    Returns:
        TextRenderer: Instance of a TextRenderer with decorators applied.
    """
    # In case it is None, default it to an empty list.
    decorators = decorators or []

    text = TextRenderer(stream=stream)
    decorators.append(TextWrapDecorator())
    text.update(decorators)

    return text
