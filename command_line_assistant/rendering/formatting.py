import re
import shutil
import textwrap


def wrap(text: str) -> str:
    """
    Wraps the input string at whitespace boundaries to fit the terminal width.
    This function is ANSI-aware and will not break ANSI escape sequences.

    Args:
        text (str): The input string.

    Returns:
        str: The wrapped string.
    """
    try:
        width = shutil.get_terminal_size().columns
    except Exception:
        width = 80  # Fallback width

    # If text contains ANSI codes, handle it specially
    if "\033[" in text:
        return _wrap_ansi_text(text, width)

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


def _wrap_ansi_text(text: str, width: int) -> str:
    """
    Wrap text that contains ANSI escape sequences.

    This function strips ANSI codes for width calculation but preserves them
    in the output.
    """
    # ANSI escape sequence pattern
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    wrapped_lines = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            wrapped_lines.append("")
        else:
            # Strip ANSI codes for width calculation
            clean_text = ansi_escape.sub("", paragraph)

            # If the clean text fits in one line, don't wrap
            if len(clean_text) <= width:
                wrapped_lines.append(paragraph)
            else:
                # For complex ANSI text that needs wrapping, we need more sophisticated logic
                # For now, just don't wrap it to avoid breaking ANSI sequences
                wrapped_lines.append(paragraph)

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
