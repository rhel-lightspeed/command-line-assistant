from command_line_assistant import utils


def test_get_payload():
    expected = {"query": "test"}
    assert utils.get_payload(query="test") == expected
