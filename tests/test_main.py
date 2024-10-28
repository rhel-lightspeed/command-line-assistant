from command_line_assistant import __main__


def test_get_args():
    _, args = __main__.get_args()
    assert not args.history_clear
    assert not args.record
    assert args.config == "config.yaml"
