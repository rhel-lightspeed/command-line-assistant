import pytest

from command_line_assistant.rendering.base import BaseStream
from command_line_assistant.rendering.renders.markdown import (
    MarkdownRenderer,
    PlainMarkdownRenderer,
)


class MockStream(BaseStream):
    def __init__(self):
        self.output = ""

    def execute(self, text: str) -> None:
        self.output = text


@pytest.fixture
def mock_stream():
    return MockStream()


@pytest.fixture
def markdown_renderer(mock_stream):
    return MarkdownRenderer(mock_stream)


@pytest.fixture
def plain_markdown_renderer(mock_stream):
    return PlainMarkdownRenderer(mock_stream)


def test_basic_text_rendering(markdown_renderer):
    text = "This is a basic text"
    markdown_renderer.render(text)
    assert "This is a basic text" in markdown_renderer._stream.output


def test_inline_code_rendering(markdown_renderer):
    text = "This is `inline code`"
    markdown_renderer.render(text)
    assert "inline code" in markdown_renderer._stream.output
    # Original markup should be removed
    assert "`inline code`" not in markdown_renderer._stream.output


def test_link_rendering(markdown_renderer):
    text = "Here's a [link](https://example.com)"
    markdown_renderer.render(text)
    assert (
        "Here's a link (\x1b[96mhttps://example.com\x1b[0m)"
        in markdown_renderer._stream.output
    )
    assert "[link](https://example.com)" not in markdown_renderer._stream.output


def test_code_block_rendering(markdown_renderer):
    text = "```python\nprint('hello')\n```"
    markdown_renderer.render(text)
    assert "Snippet" in markdown_renderer._stream.output
    assert "[python]" in markdown_renderer._stream.output
    assert "print('hello')" in markdown_renderer._stream.output


def test_multiple_code_blocks(markdown_renderer):
    text = "```python\nprint('first')\n```\nSome text\n```bash\necho 'second'\n```"
    markdown_renderer.render(text)
    assert "Snippet" in markdown_renderer._stream.output
    assert "[python]" in markdown_renderer._stream.output
    assert "[bash]" in markdown_renderer._stream.output
    assert "print('first')" in markdown_renderer._stream.output
    assert "echo 'second'" in markdown_renderer._stream.output


def test_references_rendering(markdown_renderer):
    text = "Some text\nReferences:\n1. First reference\n2. Second reference"
    markdown_renderer.render(text)
    assert "References" in markdown_renderer._stream.output
    assert "First reference" in markdown_renderer._stream.output
    assert "Second reference" in markdown_renderer._stream.output


def test_empty_text_rendering(markdown_renderer):
    markdown_renderer.render("")
    assert markdown_renderer._stream.output == ""


def test_code_block_with_empty_language(markdown_renderer):
    text = "```\nprint('hello')\n```"
    markdown_renderer.render(text)
    assert "Snippet" in markdown_renderer._stream.output
    assert "print('hello')" in markdown_renderer._stream.output


def test_code_block_with_leading_characters(markdown_renderer):
    text = "```bash\n#$ echo 'hello'\n```"
    markdown_renderer.render(text)
    assert "echo 'hello'" in markdown_renderer._stream.output


def test_section_header_formatting(markdown_renderer):
    # Testing internal method directly
    header = markdown_renderer._format_section_header("Test", "python")
    assert "[python]" in header
    assert "Test" in header
    assert "─" in header


def test_default_stream_initialization():
    renderer = MarkdownRenderer()
    assert renderer._stream is not None


def test_multiple_paragraphs(markdown_renderer):
    text = "Paragraph 1\n\nParagraph 2"
    markdown_renderer.render(text)
    assert "Paragraph 1" in markdown_renderer._stream.output
    assert "Paragraph 2" in markdown_renderer._stream.output


@pytest.mark.parametrize(
    ("text", "level", "expected"),
    (
        (
            "testing",
            1,
            """
TESTING
════════
""",
        ),
        (
            "testing",
            2,
            """
testing
────────
""",
        ),
        (
            "testing",
            3,
            """
testing
········
""",
        ),
        (
            "testing",
            99,
            """
testing
""",
        ),
    ),
)
def test_format_header(text, level, expected, markdown_renderer):
    assert markdown_renderer._format_header(text, level) == expected


def test_markdown_renderer_with_bold_italic_formatting(markdown_renderer):
    """Test that bold and italic formatting works correctly"""
    text = "This is **bold** and *italic* text"
    markdown_renderer.render(text)
    assert "bold" in markdown_renderer._stream.output
    assert "italic" in markdown_renderer._stream.output


def test_markdown_renderer_with_different_header_levels(markdown_renderer):
    """Test that different header levels render correctly"""
    text = "# Level 1 Header\n## Level 2 Header\n### Level 3 Header"
    markdown_renderer.render(text)

    output = markdown_renderer._stream.output
    assert "LEVEL 1 HEADER" in output  # Level 1 headers are uppercase
    assert "Level 2 Header" in output  # Level 2 headers have underlines
    assert "Level 3 Header" in output  # Level 3 headers have dot underlines


def test_plain_markdown_renderer(plain_markdown_renderer):
    """Test the plain markdown renderer"""
    text = "This is **bold** and *italic* text"
    plain_markdown_renderer.render(text)
    assert (
        "This is **bold** and *italic* text" in plain_markdown_renderer._stream.output
    )
