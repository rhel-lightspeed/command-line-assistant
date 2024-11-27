from argparse import Namespace

from command_line_assistant.commands import BaseCLICommand, SubParsersAction
from command_line_assistant.dbus.constants import SERVICE_IDENTIFIER
from command_line_assistant.dbus.definitions import MessageInput, MessageOutput


class QueryCommand(BaseCLICommand):
    @staticmethod
    def register_subcommand(parser: SubParsersAction):
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

        query_parser.set_defaults(func=_command_factory)

    def __init__(self, query_string: str) -> None:
        self._query = query_string
        super().__init__()

    def run(self) -> None:
        proxy = SERVICE_IDENTIFIER.get_proxy()

        input_query = MessageInput()
        input_query.message = self._query

        print("Requesting knowledge from the AI :robot:")
        proxy.ProcessQuery(MessageInput.to_structure(input_query))

        output = MessageOutput.from_structure(proxy.RetrieveAnswer).message

        if output:
            print("\n", output)


def _command_factory(args: Namespace) -> QueryCommand:
    return QueryCommand(args.query_string)
