from argparse import ArgumentParser, Namespace

from dasbus.server.template import InterfaceTemplate
from dasbus.typing import Structure

from command_line_assistant.commands import query
from command_line_assistant.dbus.definitions import MessageOutput


def test_command_factory():
    expected = "test"

    instance = query._command_factory(Namespace(query_string="test"))

    assert isinstance(instance, query.QueryCommand)
    assert instance._query == expected


def test_register_command():
    parser = ArgumentParser()
    sub_parser = parser.add_subparsers()

    query.register_subcommand(sub_parser)

    parser.parse_args(["query", "test"])


class GetProxyMock(InterfaceTemplate):
    def __new__(cls):
        return cls

    def ProcessQuery(self) -> None:
        return

    @property
    def RetrieveAnswer(self) -> Structure:
        output = MessageOutput()
        output.message = "hi"
        return MessageOutput.to_structure(output)
