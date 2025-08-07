#!/usr/bin/env python3
"""
Demo script for ANSI Markdown extensions.

This script demonstrates how to use the ANSI markdown extensions
to convert markdown to terminal-friendly output with colors.

Usage:
    python examples/ansi_markdown_demo.py

Requirements:
    pip install markdown
"""

import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main():
    """Main demo function."""
    try:
        from command_line_assistant.rendering.markdown import markdown_to_ansi
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install python-markdown: pip install markdown")
        return 1

    # Sample markdown content
    markdown_content = """
# ANSI Markdown Extensions Demo

Welcome to the **ANSI Markdown Extensions** demonstration!

## Features

This extension provides terminal-friendly rendering of markdown with:

- **Bold text** formatting
- *Italic text* formatting
- _Underlined text_ formatting
- `inline code` highlighting
- ~~Strikethrough text~~
- [Links](https://example.com) with URL display
- Multiple header levels

### Code Blocks

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("World"))
```

```bash
echo "Terminal commands work too!"
ls -la | grep "\.py$"
```

### Lists

#### Unordered List:
- First item with **bold text**
- Second item with *italic text*
- Third item with `inline code`

#### Ordered List:
1. Step one
2. Step two with [a link](https://python.org)
3. Step three

### Blockquotes

> This is a blockquote with **formatted text**.
>
> It can contain multiple paragraphs and *various* formatting.

### Tables

| Column 1     | Column 2     | Column 3     |
|--------------|--------------|--------------|
| **Bold**     | *Italic*     | `Code`       |
| Normal text  | [Link](/url) | More content |

---

### Images

![Alt text](https://example.com/image.png "Image title")

That's the demo! The extensions convert all these markdown elements
to **colorized terminal output** instead of HTML.
"""

    print("Converting markdown to ANSI formatted text...\n")
    print("=" * 60)

    # Method 1: Using the convenience function
    result = markdown_to_ansi(markdown_content)
    print(result)

    print("=" * 60)
    print(
        "\nDemo completed! The above output shows markdown converted to ANSI formatting."
    )
    print("Colors and formatting should be visible in your terminal.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
