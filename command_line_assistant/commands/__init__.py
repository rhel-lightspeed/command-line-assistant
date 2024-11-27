from abc import ABC, abstractmethod
from argparse import _SubParsersAction

# Define the type here so pyright is happy with it.
SubParsersAction = _SubParsersAction


class BaseCLICommand(ABC):
    @staticmethod
    @abstractmethod
    def register_subcommand(parser: SubParsersAction):
        raise NotImplementedError("Not implemented in base class.")

    @abstractmethod
    def run(self):
        raise NotImplementedError("Not implemented in base class.")


PARENT_ARGS = ["--version", "-v", "-h", "--help"]
ARGS_WITH_VALUES = ["--clear"]


def add_default_command(argv):
    """Add the default command when none is given"""
    args = argv

    # Early exit if we don't have any argv
    if not args:
        return args

    subcommand = _subcommand_used(argv)
    if subcommand is None:
        args.insert(0, "query")

    return args


def _subcommand_used(args):
    """Return what subcommand has been used by the user. Return None if no subcommand has been used."""
    for index, argument in enumerate(args):
        # If we have a exact match for any of the commands, return directly
        if argument in ("query", "history"):
            return argument

        # It means that we hit a --version/--help
        if argument in PARENT_ARGS:
            return argument

        # Otherwise, look for parent args
        if argument not in PARENT_ARGS and args[index - 1] in ARGS_WITH_VALUES:
            return None

    return None
