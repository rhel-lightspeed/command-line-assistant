import json
from pathlib import Path

import pytest

from command_line_assistant import history
from command_line_assistant.config import Config, HistorySchema

#: Mock history conversation for testing
MOCK_HISTORY_CONVERSATION: list[dict] = [
    {"role": "user", "content": "create a file under /etc"},
    {
        "role": "assistant",
        "content": "Sure, I can help you with that. To create a new file under the `/etc` directory in OpenShift, follow these steps:\n\n1. Log in to your OpenShift cluster using the command `oc login`.\n2. Once logged in, navigate to the project where you want to create the file. You can use the command `oc project <project_name>` to change to the desired project.\n3. Create a new file by running the command `oc create -f <filename>.yaml`. Replace `<filename>.yaml` with the name of the YAML file containing the content of the file you want to create.\n\nFor example, if you want to create a new file named `myfile` with the content `Hello, World!`, you can create the file using the following command:\n```\noc create -f myfile.yaml\n```\nThis will create a new file called `myfile` under the `/etc` directory in your OpenShift project.\n\nKeep in mind that the `oc create` command requires the `oc` command line tool to be installed and configured on your system. If you encounter any issues, please refer to the official OpenShift documentation for troubleshooting steps.",
    },
]


class TestHistoryRead:
    """Holds the testing functions for reading the history."""

    def test_not_enabled(self):
        config = Config(history=HistorySchema(enabled=False))
        assert not history.handle_history_read(config)

    def test_history_file_missing(self, tmpdir, caplog):
        history_file = tmpdir.join("non-existing-file.json")
        config = Config(history=HistorySchema(file=history_file))

        assert not history.handle_history_read(config)
        assert "File will be created with first response." in caplog.records[-1].message

    def test_history_failed_to_decode_json(self, tmpdir, caplog):
        history_file = tmpdir.join("non-existing-file.json")
        history_file.write("not a json")
        config = Config(history=HistorySchema(file=history_file))

        assert not history.handle_history_read(config)
        assert "Failed to read history file" in caplog.records[-1].message

    def test_history_read(self, tmpdir):
        history_file = tmpdir.join("history.json")
        history_file.write(json.dumps(MOCK_HISTORY_CONVERSATION))
        config = Config(history=HistorySchema(file=history_file))

        assert history.handle_history_read(config) == MOCK_HISTORY_CONVERSATION

    @pytest.mark.parametrize(
        ("multiply", "max_size"),
        (
            (
                10,
                5,
            ),
        ),
    )
    def test_history_over_max_size(self, tmpdir, multiply, max_size):
        total_mock_data = MOCK_HISTORY_CONVERSATION * multiply
        history_file = tmpdir.join("history.json")
        history_file.write(json.dumps(total_mock_data))
        config = Config(history=HistorySchema(file=history_file, max_size=max_size))

        history_result = history.handle_history_read(config)
        assert len(history_result) == max_size
        assert len(history_result) < len(total_mock_data)

        # TODO(r0x0d): Maybe include a test to check which records got back?


class TestHistoryWrite:
    def test_not_enabled(self):
        config = Config(history=HistorySchema(enabled=False))
        assert not history.handle_history_write(config, [], "")

    def test_history_file_missing(self, tmpdir):
        history_file = tmpdir.join("history").join("non-existing-file.json")
        config = Config(history=HistorySchema(file=history_file))

        history.handle_history_write(config, [], "test")
        assert Path(history_file).exists()

    def test_history_write(self, tmpdir):
        expected = [{"role": "assistant", "content": "test"}]
        history_file = tmpdir.join("history").join("non-existing-file.json")
        config = Config(history=HistorySchema(file=history_file))

        history.handle_history_write(config, [], "test")

        raw_history = Path(history_file).read_text()
        assert json.loads(raw_history) == expected

    def test_history_append(self, tmpdir):
        expected = MOCK_HISTORY_CONVERSATION.copy()
        expected.append({"role": "assistant", "content": "test"})

        history_file = tmpdir.join("history").join("non-existing-file.json")
        config = Config(history=HistorySchema(file=history_file))

        history.handle_history_write(config, MOCK_HISTORY_CONVERSATION, "test")

        raw_history = Path(history_file).read_text()
        assert json.loads(raw_history) == expected
