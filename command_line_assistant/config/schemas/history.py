"""Schemas for the history config."""

import dataclasses


@dataclasses.dataclass
class HistorySchema:
    """This class represents the [history] section of our config.toml file.

    Attributes:
        enabled (bool): Define if the history is enabled.
    """

    enabled: bool = True
