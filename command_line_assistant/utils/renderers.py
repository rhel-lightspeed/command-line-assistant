"""Utility module that provides standardized functions for rendering"""

from datetime import datetime
from typing import Optional

from command_line_assistant.rendering.base import BaseDecorator, BaseStream
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
    TextWrapDecorator,
)
from command_line_assistant.rendering.renders.interactive import InteractiveRenderer
from command_line_assistant.rendering.renders.markdown import MarkdownRenderer
from command_line_assistant.rendering.renders.spinner import SpinnerRenderer
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.rendering.stream import StderrStream, StdoutStream


def create_error_renderer() -> TextRenderer:
    """Create a standardized instance of text rendering for error output

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
    """Create a standardized instance of text rendering for error output

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
    message: str, decorators: Optional[list[BaseDecorator]] = None
) -> SpinnerRenderer:
    """Create a new instance of a spinner renderer.

    Note:
        `py:TextWrapDecorator` is applied automatically to the renderer.

    Arguments:
        message (str): The message to show while spinning
        decorators (list[BaseDecorator]): List of decorators that can be
        applied to the spinner renderer.

    Returns:
        SpinnerRenderer: Instance of a SpinnerRenderer with decorators applied.
    """
    spinner = SpinnerRenderer(message, stream=StdoutStream(end=""))
    decorators = decorators or []
    decorators.append(TextWrapDecorator())
    spinner.update(decorators)
    return spinner


def create_interactive_renderer() -> InteractiveRenderer:
    """Create a new instance of the interactive rendering.

    Returns:
        InteractiveRenderer: A new instance of the interactive renderer.
    """
    interactive = InteractiveRenderer(
        banner="Welcome to the interactive mode for command line assistant! To exit, press Ctrl + C or type '.exit'."
    )
    return interactive


def create_text_renderer(
    decorators: Optional[list[BaseDecorator]] = None,
    stream: Optional[BaseStream] = None,
) -> TextRenderer:
    """Create a new instance of a text renderer.

    Note:
        `py:TextWrapDecorator` is applied automatically to the renderer.

        If no `stream` is provided in the arguments, it will default to the
        `py:StdoutStream()`.

    Arguments:
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


def human_readable_size(size: float) -> str:
    """Converts a byte value to a human-readable format (KB, MB, GB).

    Arguments:
        size (float): The size to be converted to a human readable format

    Returns:
        str: Size in a human readable format
    """
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


def create_markdown_renderer(
    decorators: Optional[list[BaseDecorator]] = None,
    stream: Optional[BaseStream] = None,
) -> MarkdownRenderer:
    """Create a new instance of a markdown renderer.

    Arguments:
        decorators (Optional[list[BaseDecorator]], optional): List of decorators
            that can be applied to the markdown renderer. Defaults to None.
        stream (Optional[BaseStream], optional): Apply a different stream other
            than the StdoutStream. Defaults to None.

    Returns:
        MarkdownRenderer: Instance of a MarkdownRenderer with decorators applied.
    """
    decorators = decorators or []
    markdown = MarkdownRenderer(stream=stream)
    decorators.append(TextWrapDecorator())
    markdown.update(decorators)
    return markdown


def format_datetime(unformatted_date: str) -> str:
    """Format a datetime string to a more human readable format.

    Arguments:
        unformatted_date (str): The unformatted date (usually, it is datetime.now())

    Returns:
        str: The formatted date in human readable time.
    """
    # Convert str to datetime object
    date = datetime.strptime(unformatted_date, "%Y-%m-%d %H:%M:%S.%f")
    return date.strftime("%A, %B %d, %Y at %I:%M:%S %p")
