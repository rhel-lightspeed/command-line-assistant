import copy
import logging.config

from command_line_assistant.config import Config

LOGGING_CONFIG_DICTIONARY = {
    "version": 1,
    "level": "INFO",
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s: %(message)s",
            "datefmt": "%m/%d/%Y %I:%M:%S %p",
        },
        "minimal": {"format": "%(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "minimal",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "filename": "",
        },
    },
    "loggers": {"root": {"handlers": ["file"], "level": "INFO"}},
}


def setup_logging(config: Config, verbose: bool = False):
    """Setup basic logging functionality"""

    # TODO(r0x0d): This will be removed as clad will manage the logs
    if not config.logging.file.parent.exists():  # type: ignore
        config.logging.file.parent.mkdir(mode=0o755)  # type: ignore

    logging_configuration = copy.deepcopy(LOGGING_CONFIG_DICTIONARY)

    logging_configuration["handlers"]["file"]["filename"] = config.logging.file

    if verbose:
        logging_configuration["handlers"]["console"]["formatter"] = "verbose"
        logging_configuration["loggers"]["root"]["handlers"].append("console")

    logging.config.dictConfig(logging_configuration)
