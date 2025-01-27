"""Schemas for the logging config."""

import copy
import dataclasses
import pwd


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
    responses: bool = True
    question: bool = True
    users: dict[str, dict[str, bool]] = dataclasses.field(default_factory=dict)

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

        self.level = self.level.upper()

        if self.users:
            # Turn any username to their effective_user_id
            defined_users = copy.deepcopy(self.users)
            for user in defined_users.keys():
                try:
                    effective_user_id = str(pwd.getpwnam(user).pw_uid)
                    self.users[effective_user_id] = self.users.pop(user)
                except KeyError as e:
                    raise ValueError(
                        f"{user} is not present on the system. Remove it from the configuration."
                    ) from e
