import logging
import sys
from dataclasses import dataclass
from typing import Optional

from command_line_assistant.rendering.colors import Color

if sys.version_info >= (3, 11):
    pass
else:
    pass

logger = logging.getLogger(__name__)


@dataclass
class Theme:
    """A theme for the renderer.

    Attributes:
        info (Color): The color for info messages.
        warning (Color): The color for warning messages.
        notice (Color): The color for notice messages.
        error (Color): The color for error messages.
        inline_code (Color): The color for inline code.
        code_block_line (Color): The color for code block lines.
        code_block_border (Color): The color for code block borders.
        header (Color): The color for headers.
        link (Color): The color for links.
        image (Color): The color for images.
        horizontal_rule (Color): The color for horizontal rules.
    """

    # Colors for general output.
    info: Color = Color.BRIGHT_BLUE
    warning: Color = Color.YELLOW
    notice: Color = Color.BRIGHT_YELLOW
    error: Color = Color.RED

    # Colors for formatting the markdown text.
    inline_code: Color = Color.CYAN
    code_block_line: Color = Color.CYAN
    code_block_border: Color = Color.BRIGHT_RED
    header: Color = Color.GREEN
    link: Color = Color.BRIGHT_BLUE
    image: Color = Color.BRIGHT_BLUE
    horizontal_rule: Color = Color.BRIGHT_BLACK

    def __init__(self, config: Optional[dict] = None):
        """Initialize a theme.

        Args:
            config (dict): The configuration for the theme.
        """
        if config is not None:
            if "colors" in config:
                self.info = config["colors"]["info"]
                self.warning = config["colors"]["warning"]
                self.notice = config["colors"]["notice"]
                self.error = config["colors"]["error"]
            if "markdown" in config:
                self.inline_code = config["markdown"]["inline_code"]
                self.code_block_line = config["markdown"]["code_block_line"]
                self.code_block_border = config["markdown"]["code_block_border"]
                self.header = config["markdown"]["header"]
                self.link = config["markdown"]["link"]
                self.image = config["markdown"]["image"]
                self.horizontal_rule = config["markdown"]["horizontal_rule"]

            self.info = Color.from_string(self.info)
            self.warning = Color.from_string(self.warning)
            self.notice = Color.from_string(self.notice)
            self.error = Color.from_string(self.error)
            self.inline_code = Color.from_string(self.inline_code)
            self.code_block_line = Color.from_string(self.code_block_line)
            self.code_block_border = Color.from_string(self.code_block_border)
            self.header = Color.from_string(self.header)
            self.link = Color.from_string(self.link)
            self.image = Color.from_string(self.image)
            self.horizontal_rule = Color.from_string(self.horizontal_rule)
