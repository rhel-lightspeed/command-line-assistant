"""D-Bus context classes for managing the commands"""

from command_line_assistant.config import Config


class DaemonContext:
    """Context class for context that defines the structure of it."""

    def __init__(self, config: Config) -> None:
        """Constructor of the class.

        Arguments:
            config (Config): Instance of the configuration class.
        """
        self._config = config

    @property
    def config(self) -> Config:
        """Property for the internal config attribute.

        Returns:
            Config: Instance of the configuration class
        """
        return self._config
