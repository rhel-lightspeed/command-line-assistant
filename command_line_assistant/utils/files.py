"""Utilitary module to handle file operations"""

import mimetypes
from io import TextIOWrapper
from pathlib import Path
from typing import Optional


def guess_mimetype(attachment: Optional[TextIOWrapper]) -> str:
    """Guess the mimetype of a given attachment.

    Args:
        attachment (Optional[TextIOWrapper]): The attachment to be checked for mimetype.

    Returns:
        str: The guessed mimetype or "unknown/unknown" if not found.
    """
    unknown_mimetype = "unknown/unknown"

    if not attachment:
        return unknown_mimetype

    path = Path(attachment.name)
    result = mimetypes.guess_type(path)

    mimetype = result[0]
    if not mimetype:
        return unknown_mimetype

    return mimetype
