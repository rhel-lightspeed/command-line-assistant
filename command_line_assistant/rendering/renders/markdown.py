"""Module that renders markdown-formatted output to the terminal."""

import re
from dataclasses import dataclass
from typing import Optional

from command_line_assistant.rendering.base import BaseRenderer, BaseStream
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.stream import StdoutStream

# Regular expressions for markdown parsing
#: Matches inline code blocks
INLINE_CODE_REGEX = re.compile(r"`([^`]+)`")
#: Matches markdown links
HANDLE_LINKS_REGEX = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
#: Matches bold text
BOLD_REGEX = re.compile(r"\*\*(.+?)\*\*")
#: Matches italic text
ITALIC_REGEX = re.compile(r"\*(.+?)\*")
#: Matches headers
HEADER_REGEX = re.compile(r"^(#{1,6})\s+(.+)$")

# Formatting constants
#: Marker for code block start/end
CODE_BLOCK_MARKER = "```"
#: Width for section separators
SECTION_WIDTH: int = 16

# Color decorators for terminal output
HIGHLIGHT_DEFAULT_COLOR: ColorDecorator = ColorDecorator(foreground="lightblue")
LLM_RESPONSE_COLOR: ColorDecorator = ColorDecorator(foreground="red")


@dataclass
class Block:
    """Data structure representing a block of markdown content.

    Attributes:
        content (list[str]): List of strings containing the block content
        is_code (bool): Boolean indicating if this is a code block
        language (str): Programming language for code blocks
    """

    content: list[str]
    is_code: bool = False
    language: str = ""


class MarkdownRenderer(BaseRenderer):
    """Renders markdown-formatted text to the terminal with styling."""

    def __init__(self, stream: Optional[BaseStream] = None) -> None:
        """Initialize renderer with optional custom output stream.

        Args:
            stream (Optional[BaseStream], optional): Output stream to use. Defaults to stdout if not provided.
        """
        super().__init__(stream or StdoutStream())

    def _format_header(self, text: str, level: int) -> str:
        """Format a markdown header with appropriate styling.

        Args:
            text (str): Header text content
            level (str): Header level (1-3)

        Returns:
            Formatted header string
        """
        text = text.strip()
        header_styles = {
            1: (text.upper(), "═"),
            2: (text, "─"),
            3: (text, "·"),
        }
        style = header_styles.get(level, (text, ""))
        return (
            f"\n{style[0]}\n{style[1] * (len(text) + 1)}\n"
            if style[1]
            else f"\n{text}\n"
        )

    def _format_section_header(self, title: str, language: str = "") -> str:
        """Format a section header with optional language tag.

        Args:
            title (str): Section title
            language (str, optional): Optional programming language

        Returns:
            str: Formatted section header
        """
        if language:
            title = f"{HIGHLIGHT_DEFAULT_COLOR.decorate(f'[{language}]')} {title}"
        return f"{title} {'─' * SECTION_WIDTH}"

    def _process_inline_formatting(self, text: str) -> str:
        """Process inline markdown formatting (bold, italic, code, links).

        Args:
            text (str): Text to process

        Returns:
            str: Text with terminal formatting applied
        """
        formats = [
            (
                BOLD_REGEX,
                lambda m: f"\033[1m{m.group(1)}\033[0m{LLM_RESPONSE_COLOR.start()}",
            ),
            (
                ITALIC_REGEX,
                lambda m: f"\033[3m{m.group(1)}\033[0m{LLM_RESPONSE_COLOR.start()}",
            ),
            (
                INLINE_CODE_REGEX,
                lambda m: f"{HIGHLIGHT_DEFAULT_COLOR.decorate(m.group(1))}{LLM_RESPONSE_COLOR.start()}",
            ),
            (
                HANDLE_LINKS_REGEX,
                lambda m: f"{m.group(1)} ({HIGHLIGHT_DEFAULT_COLOR.decorate(m.group(2))}){LLM_RESPONSE_COLOR.start()}",
            ),
        ]

        for regex, formatter in formats:
            text = regex.sub(formatter, text)

        return LLM_RESPONSE_COLOR.decorate(text)

    def _format_code_block(self, content: str, language: str = "") -> str:
        """Format a code block with syntax highlighting.

        Args:
            content (str): Code block content
            language (str, optional): Programming language for syntax highlighting

        Returns:
            str: Formatted code block
        """
        title = "Snippet"
        header = self._format_section_header(title, language)
        content = content.strip().lstrip("$").lstrip()
        bottom_width = SECTION_WIDTH + len(title) + 1
        bottom = f"{'─' * bottom_width}"
        return f"\n{header}\n{HIGHLIGHT_DEFAULT_COLOR.decorate(content)}\n{bottom}\n"

    def _process_references(self, line: str) -> str:
        """Process reference section formatting.

        Args:
            line (str): Reference line content

        Returns:
            str: Formatted references section
        """
        title = "References"
        bottom_width = SECTION_WIDTH + len(title) + 1
        return (
            f"\n{self._format_section_header(title)}\n"
            f"{line[10:].strip()}\n"
            f"{'─' * bottom_width}\n"
        )

    def _process_blocks(self, text: str) -> list[str]:
        """Split markdown text into blocks and process each block.

        Args:
            text (str): Raw markdown text

        Returns:
            list[str]: List of processed text blocks
        """
        blocks: list[Block] = []
        current_block = Block(content=[])

        for line in text.splitlines():
            if line.startswith(CODE_BLOCK_MARKER):
                if current_block.content:
                    blocks.append(current_block)
                current_block = Block(
                    content=[],
                    is_code=not current_block.is_code,
                    language=line[3:].strip() if not current_block.is_code else "",
                )
                continue

            header_match = HEADER_REGEX.match(line)
            if header_match and not current_block.is_code:
                if current_block.content:
                    blocks.append(current_block)
                blocks.append(
                    Block(
                        content=[
                            self._format_header(
                                header_match.group(2), len(header_match.group(1))
                            )
                        ]
                    )
                )
                current_block = Block(content=[])
                continue

            if line.lower().startswith("references") and not current_block.is_code:
                if current_block.content:
                    blocks.append(current_block)
                blocks.append(Block(content=[self._process_references(line)]))
                current_block = Block(content=[])
                continue

            current_block.content.append(line)

        if current_block.content:
            blocks.append(current_block)

        return [self._format_block(block) for block in blocks if block.content]

    def _format_block(self, block: Block) -> str:
        """Format a single content block.

        Args:
            block (Block): Block to format

        Returns:
            str: Formatted block content
        """
        if block.is_code:
            return self._format_code_block("\n".join(block.content), block.language)

        text = self._process_inline_formatting("\n".join(block.content))
        return text if text.strip() else ""

    def render(self, text: str) -> None:
        """Render markdown text to the terminal.

        Args:
            text (str): Markdown formatted text to render
        """
        processed_blocks = self._process_blocks(text)
        final_text = "".join(block for block in processed_blocks if block)
        if final_text:
            self._stream.execute(final_text)
