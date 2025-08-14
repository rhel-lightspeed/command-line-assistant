from command_line_assistant.formatting import wrap


def test_wrap_text_to_terminal_width(monkeypatch):
    # Simulate a terminal width of 20 columns
    class DummyTerminalSize:
        def __init__(self, columns):
            self.columns = columns

    monkeypatch.setattr("shutil.get_terminal_size", lambda: DummyTerminalSize(20))

    # Text that contains at least two paragraphs
    text = "This is the first paragraph.\n\nThis is the second paragraph."
    wrapped = wrap(text)
    lines = wrapped.splitlines()
    assert len(lines) == 2
    assert lines[0] == "This is the first paragraph."
    assert lines[1] == "This is the second paragraph."

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
    monkeypatch.setattr(
        "shutil.get_terminal_size", lambda: (_ for _ in ()).throw(OSError())
    )
    text = "A " * 100
    wrapped = wrap(text)
    # Should wrap at 80 chars (fallback)
    assert all(len(line) <= 80 for line in wrapped.splitlines())
