import select
import sys

from command_line_assistant import utils


def test_get_payload():
    expected = {"query": "test"}
    assert utils.get_payload(query="test") == expected


def test_read_stdin(monkeypatch):
    # Mock select.select to simulate user input
    def mock_select(*args, **kwargs):
        return [sys.stdin], [], []

    monkeypatch.setattr(select, "select", mock_select)

    # Mock sys.stdin.readline to return the desired input
    monkeypatch.setattr(sys.stdin, "read", lambda: "test\n")

    assert utils.read_stdin() == "test"


def test_read_stdin_no_input(monkeypatch):
    # Mock select.select to simulate user input
    def mock_select(*args, **kwargs):
        return [], [], []

    monkeypatch.setattr(select, "select", mock_select)

    assert not utils.read_stdin()
