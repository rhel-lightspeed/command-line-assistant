import copy
import logging.config

from command_line_assistant.config import Config

LOGGING_CONFIG_DICTIONARY = {
    "version": 1,
    "disable_existing_loggers": False,
    "level": "DEBUG",
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s: %(message)s",
            "datefmt": "%m/%d/%Y %I:%M:%S %p",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {"root": {"handlers": ["console"], "level": "DEBUG"}},
}


def setup_logging(config: Config):
    """Setup basic logging functionality"""

    logging_configuration = copy.deepcopy(LOGGING_CONFIG_DICTIONARY)
    logging_configuration["loggers"]["root"]["level"] = config.logging.level

    logging.config.dictConfig(logging_configuration)
