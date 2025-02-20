"""Module that renders markdown-formatted output to the terminal."""

import re
from typing import Optional

from command_line_assistant.rendering.base import BaseRenderer, BaseStream
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.stream import StdoutStream

#: Regex to handle inline code blocks
INLINE_CODE_REGEX = re.compile(r"`([^`]+)`")
#: Regex to handle links
HANDLE_LINKS_REGEX = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
#: Regex to handle bold text
BOLD_REGEX = re.compile(r"\*\*(.+?)\*\*")
#: Regex to handle italic text
ITALIC_REGEX = re.compile(r"\*(.+?)\*")
#: Regex to handle headers
HEADER_REGEX = re.compile(r"^(#{1,6})\s+(.+)$")
#: Marker for code blocks
CODE_BLOCK_MARKER = "```"


class MarkdownRenderer(BaseRenderer):
    """Specialized class to render markdown-formatted output to the terminal."""

    def __init__(self, stream: Optional[BaseStream] = None) -> None:
        """Default constructor for class

        Arguments:
            stream (Optional[BaseStream], optional): The stream to write to. Defaults to stdout.
        """
        super().__init__(stream or StdoutStream())
        self._suggestion_count = 0
        self._section_width = 24
        self._highlight_color = ColorDecorator(foreground="lightblue")

    def _format_header(self, text: str, level: int) -> str:
        """Format a header with the appropriate styling.

        Arguments:
            text (str): The header text
            level (int): The header level (1-6)

        Returns:
            str: The formatted header
        """
        # Remove any existing formatting for clean display
        text = text.strip()

        if level == 1:
            return f"\n{text.upper()}\n{'═' * (len(text) + 1)}\n"
        elif level == 2:
            return f"\n{text}\n{'─' * (len(text) + 1)}\n"
        elif level == 3:
            return f"\n{text}\n{'·' * (len(text) + 1)}\n"
        else:
            return f"\n{text}\n"

    def _format_section_header(self, title: str, language: str = "") -> str:
        """Formats a section header with an optional language tag.

        Arguments:
            title (str): The title of the section.
            language (str, optional): The language tag to include. Defaults to "".

        Returns:
            str: The formatted section header.
        """
        if language:
            title = f"{self._highlight_color.decorate(f'[{language}]')} {title}"
        return f"{title}\n{'─' * self._section_width}"

    def _process_inline_formatting(self, text: str) -> str:
        """Processes inline formatting in the text.

        Arguments:
            text (str): The text to process.

        Returns:
            str: The processed text.
        """
        # Process bold text
        text = BOLD_REGEX.sub(lambda m: f"\033[1m{m.group(1)}\033[0m", text)

        # Process italic text
        text = ITALIC_REGEX.sub(lambda m: f"\033[3m{m.group(1)}\033[0m", text)

        # Process inline code
        text = INLINE_CODE_REGEX.sub(
            lambda m: self._highlight_color.decorate(m.group(1)), text
        )

        # Process links
        text = HANDLE_LINKS_REGEX.sub(
            lambda m: f"{m.group(1)} ({self._highlight_color.decorate(m.group(2))})",
            text,
        )

        return text

    def _format_code_block(self, content: str, language: str = "") -> str:
        """Formats a code block.

        Arguments:
            content (str): The content of the code block.
            language (str, optional): The language of the code block.

        Returns:
            str: The formatted code block.
        """
        self._suggestion_count += 1
        header = self._format_section_header(
            f"Suggestion {self._suggestion_count}", language
        )
        content = content.strip().lstrip("#$").lstrip()
        return f"\n{header}\n{self._highlight_color.decorate(content)}\n"

    def _process_references(self, line: str) -> str:
        """Formats a reference block.

        Arguments:
            line (str): The line containing the reference.

        Returns:
            str: The formatted reference block.
        """
        return (
            f"\n{self._format_section_header('References')}\n"
            f"{line[10:].strip()}\n"
            f"{'─' * self._section_width}"
        )

    def _handle_code_block(
        self, output_lines: list[str], code_content: list[str], code_language: str
    ) -> None:
        """Formats a code block.

        Arguments:
            output_lines (list[str]): The list of output lines.
            code_content (list[str]): The content of the code block.
            code_language (str): The language of the code block.
        """
        if code_content:
            output_lines.append(
                self._format_code_block("\n".join(code_content), code_language)
            )

    def _handle_text_block(
        self, output_lines: list[str], current_block: list[str]
    ) -> None:
        """Formats a text block.

        Arguments:
            output_lines (list[str]): The list of output lines.
            current_block (list[str]): The content of the text block.
        """
        if current_block:
            processed_text = self._process_inline_formatting("\n".join(current_block))
            if processed_text.strip():
                output_lines.append(processed_text)

    def _process_blocks(self, text: str) -> list[str]:
        """Processes the blocks of text and code.

        Arguments:
            text (str): The input text.

        Returns:
            list[str]: The processed output lines.
        """
        output_lines = []
        current_block = []
        code_content = []
        code_language = ""
        in_code_block = False

        for line in text.splitlines():
            # Handle headers
            header_match = HEADER_REGEX.match(line)
            if header_match and not in_code_block:
                self._handle_text_block(output_lines, current_block)
                current_block = []
                level = len(header_match.group(1))
                header_text = header_match.group(2)
                output_lines.append(self._format_header(header_text, level))
                continue

            # Handle code blocks
            if line.startswith(CODE_BLOCK_MARKER):
                if in_code_block:
                    self._handle_code_block(output_lines, code_content, code_language)
                    code_content = []
                else:
                    self._handle_text_block(output_lines, current_block)
                    current_block = []
                    code_language = line[3:].strip()
                in_code_block = not in_code_block
                continue

            # Process the line based on context
            if in_code_block:
                code_content.append(line)
            elif line.lower().startswith("references"):
                self._handle_text_block(output_lines, current_block)
                current_block = []
                output_lines.append(self._process_references(line))
            else:
                current_block.append(line)

        # Handle any remaining blocks
        if in_code_block and code_content:
            self._handle_code_block(output_lines, code_content, code_language)
        elif current_block:
            self._handle_text_block(output_lines, current_block)

        return output_lines

    def render(self, text: str) -> None:
        """Render markdown-formatted text with decorators applied.

        Arguments:
            text (str): The markdown text to render
        """
        self._suggestion_count = 0
        processed_blocks = self._process_blocks(text)
        final_text = "".join(block for block in processed_blocks if block)
        if final_text:
            self._stream.execute(final_text)
