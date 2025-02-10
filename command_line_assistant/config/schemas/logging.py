"""Schemas for the logging config."""

import dataclasses


@dataclasses.dataclass
class AuditSchema:
    """This class represents the [logging.audit] section of our config.toml file.

    Attributes:
        enabled (bool): Flag to control if the logging should be enabled or not.
    """

    enabled: bool = True


@dataclasses.dataclass
class LoggingSchema:
    """This class represents the [logging] section of our config.toml file.

    Attributes:
        level (str): The level to log. Defaults to "INFO".
        responses (bool): If the responses should be logged. Defaults to True.
        question (bool): If the questions should be logged. Defaults to True.
        users (dict[str, dict[str, bool]]): A dictionary of users and their logging preferences.
    """

    level: str = "INFO"
    audit: AuditSchema = dataclasses.field(default_factory=AuditSchema)

    def __post_init__(self) -> None:
        """Post initialization method to normalize values

        Raises:
            ValueError: In case the requested level i snot in the allowed_levels list.
        """
        level = self.level.upper()
        allowed_levels = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET")
        if level not in allowed_levels:
            raise ValueError(
                f"The requested level '{level}' is not allowed. Choose from: {', '.join(allowed_levels)}"
            )

        self.level = level

        if isinstance(self.audit, dict):
            self.audit = AuditSchema(**self.audit)
