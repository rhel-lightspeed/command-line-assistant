from argparse import Namespace

from command_line_assistant.commands import BaseCLICommand, SubParsersAction


class HistoryCommand(BaseCLICommand):
    @staticmethod
    def register_subcommand(parser: SubParsersAction):
        """
        Register this command to argparse so it's available for the datasets-cli

        Args:
            parser: Root parser to register command-specific arguments
        """
        history_parser = parser.add_parser(
            "history",
            help="Manage conversation history",
        )
        history_parser.add_argument(
            "--clear", action="store_true", help="Clear the history."
        )
        history_parser.set_defaults(func=_command_factory)

    def __init__(self, clear: bool) -> None:
        self._clear = clear
        super().__init__()

    def run(self) -> None:
        print(self._clear)


def _command_factory(args: Namespace) -> HistoryCommand:
    return HistoryCommand(args.clear)
