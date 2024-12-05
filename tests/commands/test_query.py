from argparse import ArgumentParser, Namespace

from command_line_assistant.commands import query


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
