"""
Python-Markdown extensions that process a document and add ANSI color codes to
the output.

This module provides a set of extensions for python-markdown that render
markdown elements using ANSI escape codes suitable for terminal display.
"""

import re
from typing import Dict, List, Optional
from xml.etree import ElementTree as etree

import markdown
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

from command_line_assistant.rendering.colors import Color, Style, colorize, stylize
from command_line_assistant.rendering.formatting import wrap


class ANSIRenderer:
    """Base ANSI renderer that provides common formatting utilities."""

    pass  # No initialization needed

    def bold(self, text: str) -> str:
        """Format text as bold."""
        return stylize(text, Style.BOLD)

    def italic(self, text: str) -> str:
        """Format text as italic."""
        return stylize(text, Style.ITALIC)

    def underline(self, text: str) -> str:
        """Format text as underlined."""
        return stylize(text, Style.UNDERLINE)

    def strikethrough(self, text: str) -> str:
        """Format text as strikethrough."""
        return stylize(text, Style.STRIKETHROUGH)

    def code_inline(self, text: str) -> str:
        """Format inline code."""
        return colorize(text, Color.CYAN)

    def code_block(self, text: str, language: str = "") -> str:
        """Format code block."""
        lang_text = f" {language} snippet " if language else ""
        lines = [colorize(line, Color.CYAN) for line in text.rstrip().split("\n")]
        longest_line_length = max(len(line) for line in text.rstrip().split("\n"))
        padding = longest_line_length - len(lang_text) + 6
        header = colorize(f"──{lang_text}{'─' * padding}", Color.BRIGHT_RED)
        footer = colorize(f"{'─' * (padding + len(lang_text) + 2)}", Color.BRIGHT_RED)
        return f"\n{header}\n" + "\n".join(lines) + f"\n{footer}\n"

    def header(self, text: str, level: int) -> str:
        """Format header."""
        prefix = "#" * level
        return f"\n{colorize(f'{prefix} {text}', Color.GREEN)}\n"

    def link(self, text: str, url: str, title: str = "") -> str:
        """Format link."""
        link_text = colorize(text, Color.BRIGHT_BLUE)
        if title:
            return f"{link_text} ({colorize(url, Color.BRIGHT_BLUE)}, {title})"
        return f"{link_text} ({colorize(url, Color.BRIGHT_BLUE)})"

    def image(self, alt_text: str, url: str, title: str = "") -> str:
        """Format image (as text representation)."""
        return f"[Image: {alt_text}] ({colorize(url, Color.BRIGHT_BLUE)})"

    def blockquote(self, text: str) -> str:
        """Format blockquote."""
        lines = text.strip().split("\n")
        quoted_lines = [f"│ {line}" for line in lines]
        return "\n".join(quoted_lines)

    def list_item(self, text: str, ordered: bool = False, index: int = 1) -> str:
        """Format list item."""
        if ordered:
            marker = f"{index}."
        else:
            marker = "•"
        return f"{marker} {text}"

    def horizontal_rule(self) -> str:
        """Format horizontal rule."""
        return f"\n{colorize('─' * 60, Color.BRIGHT_BLACK)}\n"

    def format_table(self, rows: List[List[str]], header_row: bool = True) -> str:
        """Format a complete table with proper column alignment."""
        if not rows:
            return ""

        # Calculate column widths
        num_cols = len(rows[0])
        col_widths = []

        for col in range(num_cols):
            max_width = 0
            for row in rows:
                if col < len(row):
                    # Remove ANSI codes for width calculation
                    clean_text = self._strip_ansi(row[col])
                    max_width = max(max_width, len(clean_text))
            # Minimum width of 3, add padding
            col_widths.append(max(3, max_width + 2))

        result = []

        # Top border
        top_border = "┌"
        for i, width in enumerate(col_widths):
            top_border += "─" * width
            if i < len(col_widths) - 1:
                top_border += "┬"
        top_border += "┐"
        result.append(top_border)

        # Process each row
        for row_idx, row in enumerate(rows):
            # Format cells
            formatted_cells = []
            for col, cell in enumerate(row):
                if col < len(col_widths):
                    clean_text = self._strip_ansi(cell)
                    padding = col_widths[col] - len(clean_text)
                    left_pad = padding // 2
                    right_pad = padding - left_pad

                    if row_idx == 0 and header_row:
                        # Header cell
                        formatted_cell = f"{' ' * left_pad}{colorize(cell, Color.GREEN)}{' ' * right_pad}"
                    else:
                        # Regular cell
                        formatted_cell = f"{' ' * left_pad}{cell}{' ' * right_pad}"
                    formatted_cells.append(formatted_cell)

            # Row content
            row_content = "│"
            row_content += "│".join(formatted_cells)
            row_content += "│"
            result.append(row_content)

            # Add separator after header
            if row_idx == 0 and header_row and len(rows) > 1:
                sep_border = "├"
                for i, width in enumerate(col_widths):
                    sep_border += "─" * width
                    if i < len(col_widths) - 1:
                        sep_border += "┼"
                sep_border += "┤"
                result.append(sep_border)

        # Bottom border
        bottom_border = "└"
        for i, width in enumerate(col_widths):
            bottom_border += "─" * width
            if i < len(col_widths) - 1:
                bottom_border += "┴"
        bottom_border += "┘"
        result.append(bottom_border)

        return "\n" + "\n".join(result) + "\n"

    def _strip_ansi(self, text: str) -> str:
        """Strip ANSI escape codes from text for width calculation."""
        import re

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)


class FencedCodeBlockProcessor(BlockProcessor):
    """Block processor that handles fenced code blocks and converts them to <pre><code> elements."""

    # Pattern to match opening fence
    FENCE_START_RE = re.compile(r"^```(\w*).*$", re.MULTILINE)
    # Pattern to match closing fence
    FENCE_END_RE = re.compile(r"^```\s*$", re.MULTILINE)

    def test(self, parent, block):
        """Test if this block starts a fenced code block."""
        return self.FENCE_START_RE.match(block) is not None

    def run(self, parent, blocks):
        """Process fenced code blocks."""
        if not blocks:
            return False

        first_block = blocks[0]

        # Check if this block starts with a fence
        start_match = self.FENCE_START_RE.match(first_block)
        if not start_match:
            return False

        # Extract language from the first line
        language = start_match.group(1) or ""

        # Check if the closing fence is in the same block
        if self.FENCE_END_RE.search(first_block):
            # Entire code block is in one block
            blocks.pop(0)

            lines = first_block.split("\n")
            code_lines = []
            in_code = False

            for line in lines:
                if self.FENCE_START_RE.match(line) and not in_code:
                    in_code = True
                    continue
                elif self.FENCE_END_RE.match(line) and in_code:
                    break
                elif in_code:
                    code_lines.append(line)

            # Create the <pre><code> structure
            pre_elem = etree.SubElement(parent, "pre")
            code_elem = etree.SubElement(pre_elem, "code")

            # Add language class if specified
            if language:
                code_elem.set("class", f"language-{language}")

            # Join all code lines
            code_content = "\n".join(code_lines).rstrip()
            code_elem.text = code_content

            return True

        # Code block spans multiple blocks
        # Remove the first block and start collecting content
        blocks.pop(0)
        code_parts = []

        # Get the content after the opening fence in the first block
        first_lines = first_block.split("\n")[1:]  # Skip the ```language line
        first_content = "\n".join(first_lines)
        code_parts.append(first_content)

        # Look for the closing fence in subsequent blocks
        while blocks:
            current_block = blocks[0]

            # Check if this block contains the closing fence
            if self.FENCE_END_RE.search(current_block):
                blocks.pop(0)

                # Add lines before the closing fence
                lines = current_block.split("\n")
                final_lines = []
                for line in lines:
                    if self.FENCE_END_RE.match(line):
                        break
                    final_lines.append(line)

                if final_lines:
                    final_content = "\n".join(final_lines)
                    code_parts.append(final_content)

                # Create the <pre><code> structure
                pre_elem = etree.SubElement(parent, "pre")
                code_elem = etree.SubElement(pre_elem, "code")

                # Add language class if specified
                if language:
                    code_elem.set("class", f"language-{language}")

                # Join code parts with empty lines to restore consumed empty lines
                # Each block boundary represents a consumed empty line in the original
                code_content = "\n\n".join(code_parts).rstrip()
                code_elem.text = code_content

                return True
            else:
                # This entire block is part of the code
                blocks.pop(0)
                code_parts.append(current_block)

        # If we get here, we didn't find a closing fence
        # Put the blocks back and let normal processing handle it
        blocks.insert(0, first_block)
        for block in reversed(
            code_parts[1:]
        ):  # Skip the first part as it's part of first_block
            blocks.insert(1, block)

        return False


class ANSITreeProcessor(Treeprocessor):
    """Tree processor that converts HTML elements to ANSI formatted text."""

    def __init__(self, md: markdown.Markdown, renderer: ANSIRenderer):
        super().__init__(md)
        self.renderer = renderer
        self.parent_map: Dict[etree.Element, etree.Element] = {}
        self.list_counters: Dict[etree.Element, int] = {}

    def run(self, root: etree.Element) -> None:
        """Process the element tree and convert to ANSI text."""
        # First pass: set up parent relationships
        self._set_parent_relationships(root)

        text = self._process_element(root)
        # Replace the root with a single text node
        root.clear()
        root.text = text
        root.tag = "div"  # Use a neutral container

    def _set_parent_relationships(
        self, elem: etree.Element, parent: Optional[etree.Element] = None
    ) -> None:
        """Set parent relationships for all elements."""
        if parent is not None:
            self.parent_map[elem] = parent
        for child in elem:
            self._set_parent_relationships(child, elem)

    def _process_element(self, elem: etree.Element) -> str:
        """Process a single element and its children."""
        tag = elem.tag.lower()
        text = elem.text or ""
        tail = elem.tail or ""

        # Process children first
        child_text = ""
        for child in elem:
            child_text += self._process_element(child)

        # Combine text content
        content = text + child_text

        # Apply formatting based on tag
        formatted = self._format_by_tag(tag, elem, content)

        return formatted + tail

    def _format_by_tag(self, tag: str, elem: etree.Element, content: str) -> str:
        """Format content based on HTML tag."""
        # Text formatting tags
        if tag in ("strong", "b"):
            return self.renderer.bold(wrap(content))
        elif tag in ("em", "i"):
            return self.renderer.italic(wrap(content))
        elif tag == "u":
            return self.renderer.underline(wrap(content))
        elif tag in ("del", "s"):
            return self.renderer.strikethrough(wrap(content))
        elif tag == "code":
            # Check if this is inside a <pre> element (code block) or standalone (inline code)
            parent = self.parent_map.get(elem)
            if parent is not None and parent.tag.lower() == "pre":
                # This is handled by the <pre> case, just return content
                return content
            else:
                # This is inline code
                return self.renderer.code_inline(content)

        # Block elements
        elif tag == "pre":
            return self._format_code_block(elem, wrap(content))
        elif self._is_header_tag(tag):
            level = int(tag[1])
            return self.renderer.header(wrap(content), level)
        elif tag == "blockquote":
            return self.renderer.blockquote(wrap(content))
        elif tag == "hr":
            return self.renderer.horizontal_rule()
        elif tag == "p":
            return f"{wrap(content)}\n" if content.strip() else ""

        # Links and media
        elif tag == "a":
            return self._format_link(elem, wrap(content))
        elif tag == "img":
            return self._format_image(elem)

        # Lists and tables
        elif tag == "li":
            return self._format_list_item(elem, wrap(content))
        elif tag in ("ul", "ol"):
            return wrap(content)
        elif tag == "table":
            return self._format_table(elem)
        elif tag in ("thead", "tbody", "td", "th"):
            return wrap(content)
        elif tag == "tr":
            # Table rows are handled by _format_table
            return wrap(content)

        # Other elements
        elif tag == "br":
            return "\n"
        else:
            return wrap(content)

    def _is_header_tag(self, tag: str) -> bool:
        """Check if tag is a header tag (h1-h6)."""
        return tag.startswith("h") and len(tag) == 2 and tag[1].isdigit()

    def _format_code_block(self, elem: etree.Element, content: str) -> str:
        """Format code block element."""
        code_elem = elem.find("code")
        if code_elem is not None:
            language = code_elem.get("class", "").replace("language-", "")
            return self.renderer.code_block(code_elem.text or "", language)
        else:
            return self.renderer.code_block(content)

    def _format_link(self, elem: etree.Element, content: str) -> str:
        """Format link element."""
        url = elem.get("href", "")
        title = elem.get("title", "")
        return self.renderer.link(content, url, title)

    def _format_image(self, elem: etree.Element) -> str:
        """Format image element."""
        alt = elem.get("alt", "")
        src = elem.get("src", "")
        title = elem.get("title", "")
        return self.renderer.image(alt, src, title)

    def _format_list_item(self, elem: etree.Element, content: str) -> str:
        """Format list item element, determining if it's ordered or unordered."""
        parent = self.parent_map.get(elem)
        if parent is None:
            # No parent found, default to unordered
            return self.renderer.list_item(content, ordered=False, index=1)

        parent_tag = parent.tag.lower()
        if parent_tag == "ol":
            # Ordered list - need to track the index
            if parent not in self.list_counters:
                self.list_counters[parent] = 0

            self.list_counters[parent] += 1
            index = self.list_counters[parent]
            return self.renderer.list_item(content, ordered=True, index=index)
        elif parent_tag == "ul":
            # Unordered list
            return self.renderer.list_item(content, ordered=False, index=1)
        else:
            # Unknown parent, default to unordered
            return self.renderer.list_item(content, ordered=False, index=1)

    def _format_table(self, elem: etree.Element) -> str:
        """Format entire table element with proper column alignment."""
        rows = []
        has_header = False

        # Process all rows in the table
        for row_elem in elem.findall(".//tr"):
            cells = []
            row_has_th = False

            # Get all cells in this row
            for cell_elem in row_elem.findall(".//td") + row_elem.findall(".//th"):
                cell_content = self._process_element(cell_elem)
                # Clean up cell content - remove extra whitespace and newlines
                cell_content = cell_content.strip().replace("\n", " ")
                cells.append(cell_content)
                if cell_elem.tag.lower() == "th":
                    row_has_th = True

            if cells:  # Only add non-empty rows
                rows.append(cells)
                if row_has_th:
                    has_header = True

        if not rows:
            return ""

        return self.renderer.format_table(rows, header_row=has_header)


class ANSIExtension(Extension):
    """Main Python-Markdown extension that provides ANSI terminal output."""

    def __init__(self, **kwargs):
        self.config = {
            "renderer": [ANSIRenderer(), "ANSI renderer instance"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        """Register the ANSI processors."""
        renderer = self.getConfig("renderer")

        # Register the fenced code block processor (run before other block processors)
        fenced_processor = FencedCodeBlockProcessor(md.parser)
        md.parser.blockprocessors.register(fenced_processor, "fenced_code", 25)

        # Register the tree processor (run last)
        tree_processor = ANSITreeProcessor(md, renderer)
        md.treeprocessors.register(tree_processor, "ansi", 0)


# Convenience functions
def markdown_to_ansi(text: str, **kwargs) -> str:
    """Convert markdown text to ANSI formatted text.

    Args:
        text: Markdown text to convert
        **kwargs: Additional arguments passed to markdown.markdown()

    Returns:
        ANSI formatted text suitable for terminal display
    """

    md = ANSIMarkdown(**kwargs)
    return md.convert(text)


class ANSIMarkdown(markdown.Markdown):
    """Markdown processor that converts markdown to ANSI formatted text. This
    is a convenience class that can be used in place of a markdown.Markdown
    instance to render markdown to ANSI formatted text suitable for terminal
    display."""

    def __init__(self, **kwargs):
        super().__init__(extensions=[ANSIExtension(), "tables"], **kwargs)
