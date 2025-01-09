"""Utilitary module to handle file operations"""

from typing import Union

#: Common binary signatures
BINARY_SIGNATURES = [
    b"\x7fELF",  # ELF files
    b"%PDF",  # PDF files
    b"PK\x03\x04",  # ZIP files
]


def is_content_in_binary_format(content: Union[str, bytes]) -> bool:
    """Check if a given content is in binary format.

    Args:
        content (str): The content to be checked for binary presence.

    Raises:
        ValueError: If the content is binary or contains invalid text encoding.

    Returns:
        bool: True if the content is binary, False otherwise.
    """
    try:
        # Try to decode as utf-8
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        # Check for null bytes which often indicate binary data
        if "\0" in content:
            return True

        # Additional check for common binary file signatures
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        if any(content_bytes.startswith(sig) for sig in BINARY_SIGNATURES):
            return True
    except UnicodeDecodeError as e:
        raise ValueError(
            "File appears to be binary or contains invalid text encoding"
        ) from e

    return False
