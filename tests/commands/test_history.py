from argparse import ArgumentParser, Namespace

from command_line_assistant.commands import history


def test_command_factory():
    expected = True

    instance = history._command_factory(Namespace(clear=True))

    assert isinstance(instance, history.HistoryCommand)
    assert instance._clear == expected


def test_register_command():
    parser = ArgumentParser()
    sub_parser = parser.add_subparsers()

    history.register_subcommand(sub_parser)

    parser.parse_args(["history", "--clear"])


def test_run():
    command = history.HistoryCommand(clear=True)
    command.run()
