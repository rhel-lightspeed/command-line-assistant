import pytest

from command_line_assistant.utils.files import is_content_in_binary_format


@pytest.mark.parametrize(
    ("content", "expected"),
    (
        ("some random string", False),
        ("\0", True),
        (b"\x7fELF test elf file", True),
        (b"%PDF test pdf file", True),
        (b"PK\x03\x04 test zip", True),
    ),
)
def test_is_content_in_binary_format(content, expected):
    assert is_content_in_binary_format(content) == expected


def test_is_content_in_binary_format_decode_error():
    with pytest.raises(
        ValueError, match="File appears to be binary or contains invalid text encoding"
    ):
        is_content_in_binary_format(b"\x80")
