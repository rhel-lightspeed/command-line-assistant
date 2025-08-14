import shutil
import textwrap


def wrap(text: str) -> str:
    """
    Wraps the input string at whitespace boundaries to fit the terminal width.

    Args:
        text (str): The input string.

    Returns:
        str: The wrapped string.
    """
    try:
        width = shutil.get_terminal_size().columns
    except Exception:
        width = 80  # Fallback width

    # textwrap.wrap returns a list of lines
    wrapped_lines = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            # Preserve empty lines
            wrapped_lines.append("")
        else:
            wrapped_lines.extend(
                textwrap.wrap(
                    paragraph,
                    width=width,
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )
    return "\n".join(wrapped_lines)


def truncate(text: str, placeholder: str = "") -> str:
    """
    Truncates the input string to fit the terminal width.

    Args:
        text (str): The input string.
        placeholder (str): The placeholder string to use when truncating.

    Returns:
        str: The truncated string.
    """
    try:
        width = shutil.get_terminal_size().columns
    except Exception:
        width = 80  # Fallback width

    return textwrap.shorten(text, width=width, placeholder=placeholder)
