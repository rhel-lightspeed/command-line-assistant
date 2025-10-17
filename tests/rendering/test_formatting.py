from command_line_assistant.rendering.formatting import wrap


def test_wrap_text_to_terminal_width(monkeypatch):
    # Simulate a terminal width of 20 columns
    class DummyTerminalSize:
        def __init__(self, columns):
            self.columns = columns

        def __iter__(self):
            # Allow unpacking as (width, height)
            return iter((self.columns, 24))

    monkeypatch.setattr(
        "shutil.get_terminal_size", lambda fallback=(80, 24): DummyTerminalSize(20)
    )

    # Text that contains at least two paragraphs
    text = "This is the first paragraph.\n\nThis is the second paragraph."
    wrapped = wrap(text)
    lines = wrapped.splitlines()
    # The text should be wrapped because each paragraph is longer than 20 chars
    # First paragraph: "This is the first paragraph." (29 chars) -> wrapped
    # Second paragraph: "This is the second paragraph." (30 chars) -> wrapped
    # Plus there should be an empty line between paragraphs
    assert (
        len(lines) == 5
    )  # 2 lines for first paragraph + empty line + 2 lines for second paragraph
    assert lines[0] == "This is the first"
    assert lines[1] == "paragraph."
    assert lines[2] == ""  # Empty line between paragraphs
    assert lines[3] == "This is the second"
    assert lines[4] == "paragraph."

    # Text that should wrap at whitespace boundaries
    text = "This is a long line that should be wrapped at whitespace boundaries to fit the terminal width."
    wrapped = wrap(text)
    lines = wrapped.splitlines()
    # All lines should be <= 20 chars
    assert all(len(line) <= 20 for line in lines)
    # The text should not be broken in the middle of a word
    for line in lines:
        assert not line.startswith(" "), "No line should start with a space"
        assert not line.endswith(" "), "No line should end with a space"

    # Test that empty lines are preserved
    text_with_empty = (
        "First paragraph.\n\nSecond paragraph with more text that should wrap."
    )
    wrapped = wrap(text_with_empty)
    assert "" in wrapped.splitlines()

    # Test fallback width (simulate get_terminal_size raising)
    def mock_get_terminal_size_error(fallback=(80, 24)):
        raise OSError()

    with monkeypatch.context() as m:
        m.setattr("shutil.get_terminal_size", mock_get_terminal_size_error)
        text = "A " * 100
        wrapped = wrap(text)
        # Should wrap at 80 chars (fallback)
        assert all(len(line) <= 80 for line in wrapped.splitlines())
