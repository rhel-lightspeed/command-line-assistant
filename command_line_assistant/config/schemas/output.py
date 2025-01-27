"""Schemas for the output config."""

import dataclasses
from pathlib import Path
from typing import Union


@dataclasses.dataclass
class OutputSchema:
    """This class represents the [output] section of our config.toml file.

    Attributes:
        enforce_script (bool): If the script should be enforced.
        file (Union[str, Path]): The filepath for the script output.
        prompt_separator (str): Define the character for the prompt separator
    """

    enforce_script: bool = False
    file: Union[str, Path] = Path("/tmp/command-line-assistant_output.txt")  # type: ignore
    prompt_separator: str = "$"

    def __post_init__(self):
        """Post initialization method to normalize values"""
        self.file: Path = Path(self.file).expanduser()
