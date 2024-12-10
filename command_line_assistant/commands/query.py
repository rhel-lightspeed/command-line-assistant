from argparse import Namespace

from command_line_assistant.config import Config
from command_line_assistant.handlers import handle_query
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction


class QueryCommand(BaseCLICommand):
    def __init__(self, query_string: str, config: Config) -> None:
        self._query = query_string
        self._config = config
        super().__init__()

    def run(self) -> None:
        handle_query(self._query, self._config)


def register_subcommand(parser: SubParsersAction, config: Config) -> None:
    """
    Register this command to argparse so it's available for the datasets-cli

    Args:
        parser: Root parser to register command-specific arguments
    """
    query_parser = parser.add_parser(
        "query",
        help="",
    )
    # Positional argument, required only if no optional arguments are provided
    query_parser.add_argument(
        "query_string", nargs="?", help="Query string to be processed."
    )

    # TODO(r0x0d): This is temporary as it will get removed
    query_parser.set_defaults(func=lambda args: _command_factory(args, config))


def _command_factory(args: Namespace, config: Config) -> QueryCommand:
    return QueryCommand(args.query_string, config)
