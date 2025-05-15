from argparse import ArgumentParser, Namespace
from datetime import datetime
from unittest import mock
from unittest.mock import patch

import pytest

from command_line_assistant.commands import chat
from command_line_assistant.commands.chat import (
    ALWAYS_LEGAL_MESSAGE,
    BaseChatOperation,
    ChatCommand,
    InteractiveChatOperation,
    SingleQuestionOperation,
    _command_factory,
    _get_input_source,
    _parse_attachment_file,
    _read_last_terminal_output,
    register_subcommand,
)
from command_line_assistant.dbus.exceptions import (
    ChatNotFoundError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.structures.chat import ChatEntry, ChatList, Response
from command_line_assistant.exceptions import ChatCommandException, StopInteractiveMode
from command_line_assistant.utils.files import NamedFileLock
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_text_renderer,
)


@pytest.fixture
def base_chat_question_operation(default_kwargs):
    return BaseChatOperation(**default_kwargs)


@pytest.fixture
def default_namespace():
    return Namespace(
        query_string="",
        stdin="",
        attachment="",
        interactive=False,
        list="",
        delete="",
        delete_all=False,
        name="test",
        description="test",
        with_output=None,
        plain=False,
    )


def test_chat_command_initialization(default_namespace):
    command = ChatCommand(default_namespace)
    assert command._args == default_namespace


@pytest.mark.parametrize(
    (
        "test_input",
        "expected_output",
    ),
    [
        ("how to list files?", "Use the ls command"),
        ("what is linux?", "Linux is an operating system"),
        ("test!@#$%^&*()_+ query", "response with special chars !@#%"),
    ],
)
def test_chat_command_run_single_question(
    mock_dbus_service,
    test_input,
    expected_output,
    capsys,
    default_namespace,
    command_context,
):
    mock_dbus_service.GetUserId.return_value = "test-user"
    mock_dbus_service.CreateChat.return_value = "test-chat"
    mock_dbus_service.AskQuestion.return_value = Response(expected_output).structure()

    default_namespace.query_string = test_input
    command = ChatCommand(default_namespace)
    command._context = command_context
    command.run()

    captured = capsys.readouterr()
    assert expected_output in captured.out


@pytest.mark.parametrize(
    (
        "query_string",
        "stdin",
        "expected",
    ),
    (
        ("h", "", "Your query needs to have at least 2 characters."),
        ("", "h", "Your stdin input needs to have at least 2 characters."),
        ("h", "h", "Your query needs to have at least 2 characters."),
    ),
)
def test_chat_command_run_minimum_characters(
    query_string,
    stdin,
    expected,
    capsys,
    default_namespace,
):
    default_namespace.query_string = query_string
    default_namespace.stdin = stdin
    command = ChatCommand(default_namespace)
    assert command.run() == 80

    captured = capsys.readouterr()
    assert expected in captured.err.strip()


def test_register_subcommand():
    """Test register_subcommand function"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # Register the subcommand
    register_subcommand(subparsers)

    # Parse a test command
    args = parser.parse_args(["chat", "test query"])

    assert args.query_string == "test query"
    assert hasattr(args, "func")


@pytest.mark.parametrize(
    ("query_string", "stdin", "attachment"),
    (
        (
            "test query",
            "",
            "",
        ),
        (
            "",
            "stdin",
            "",
        ),
        ("", "", mock.MagicMock()),
        ("test query", "test stdin", mock.MagicMock()),
    ),
)
def test_command_factory(query_string, stdin, attachment, default_namespace):
    """Test _command_factory function"""
    default_namespace.query_string = query_string
    default_namespace.stdin = stdin
    default_namespace.attachment = attachment
    command = _command_factory(default_namespace)

    assert isinstance(command, ChatCommand)
    assert command._args.query_string == query_string
    assert command._args.stdin == stdin


@pytest.mark.parametrize(
    ("args", "expected"),
    (
        (
            {"with_output": 9},
            "Original index is 9",
        ),
        (
            {"with_output": -1},
            "Original index is -1",
        ),
    ),
)
def test_command_factory_with_output_normalization(
    args, expected, default_namespace, caplog
):
    default_namespace.with_output = args["with_output"]

    command = _command_factory(default_namespace)

    assert isinstance(command, ChatCommand)

    assert expected in caplog.records[-1].message
    assert command._args.with_output == -abs(args["with_output"])


def test_command_factory_missing_description_and_name(default_namespace, caplog):
    """Test _command_factory function with missing description and name"""
    default_namespace.description = ""
    default_namespace.name = ""

    command = _command_factory(default_namespace)

    assert isinstance(command, ChatCommand)

    assert (
        "No name or description provided. Using default values."
        in caplog.records[-1].message
    )
    assert command._args.description == "Default Command Line Assistant Chat."
    assert command._args.name == "default"


@pytest.mark.parametrize(
    ("args", "expected"),
    (
        (
            {"description": "test", "name": ""},
            "Chat name not provided.",
        ),
        (
            {"description": "", "name": "test"},
            "Chat description not provided.",
        ),
    ),
)
def test_command_factory_validations(args, expected, capsys, default_namespace):
    default_namespace.description = args["description"]
    default_namespace.name = args["name"]

    command = _command_factory(default_namespace)

    assert isinstance(command, ChatCommand)

    captured = capsys.readouterr()
    assert expected in captured.err.strip()


@pytest.mark.parametrize(
    ("query_string", "stdin", "attachment", "last_output", "expected"),
    (
        ("test query", None, None, "", "test query"),
        (None, "stdin", None, "", "stdin"),
        ("query", "stdin", None, "", "query stdin"),
        (None, None, "file query", "", "file query"),
        ("query", None, "file query", "", "query file query"),
        (None, "stdin", "file query", "", "stdin file query"),
        (None, None, None, "last output", "last output"),
        ("query", None, "attachment", "last output", "query attachment last output"),
        # Stdin in this case is ignored.
        ("test query", "test stdin", "file query", "", "test query file query"),
    ),
)
def test_get_input_source(
    query_string, stdin, attachment, last_output, expected, tmp_path, default_namespace
):
    """Test _command_factory function"""
    file_attachment = None

    if attachment:
        file_attachment = tmp_path / "test.txt"
        file_attachment.write_text(attachment)
        file_attachment = open(file_attachment, "r")

    output = _get_input_source(query_string, stdin, attachment, last_output)

    assert output == expected


def test_get_inout_source_all_values_warning_message(tmp_path, caplog):
    file_attachment = tmp_path / "test.txt"
    file_attachment.write_text("file")
    file_attachment = open(file_attachment, "r")
    query_string = "query"
    stdin = "stdin"
    attachment = file_attachment.read()

    output = _get_input_source(query_string, stdin, attachment, "last_output")

    assert output == "query file"
    assert (
        "Using positional query and file input. Stdin will be ignored."
        in caplog.records[-1].message
    )


def test_get_input_source_value_error():
    with pytest.raises(
        ValueError,
        match="No input provided. Please provide input via file, stdin, or direct query.",
    ):
        _get_input_source("", "", "", "")


@pytest.mark.parametrize(
    ("exception", "expected"),
    (
        (
            ChatCommandException("Test DBus Error"),
            "Test DBus Error",
        ),
    ),
)
def test_dbus_error_handling(
    exception, expected, mock_dbus_service, capsys, default_namespace
):
    """Test handling of DBus errors"""
    # Make AskQuestion raise a DBus error
    mock_dbus_service.AskQuestion.side_effect = exception
    default_namespace.query_string = "test query"
    command = ChatCommand(default_namespace)
    command.run()

    # Verify error message in stdout
    captured = capsys.readouterr()
    assert expected in captured.err.strip()


@pytest.mark.parametrize(
    ("content", "expected"),
    (
        ("test", "test"),
        ("test ", "test"),
    ),
)
def test_parse_attachment_file(content, expected, tmp_path):
    file_attachment = tmp_path / "file.txt"
    file_attachment.write_text(content)
    file_attachment = open(file_attachment, mode="r")

    assert _parse_attachment_file(file_attachment) == expected


def test_parse_attachment_file_missing():
    assert not _parse_attachment_file(None)


def test_parse_attachment_file_exception(tmp_path):
    file_attachment = tmp_path / "file.txt"
    file_attachment.write_bytes(b"'\x80abc'")
    file_attachment = open(file_attachment, mode="r")

    with pytest.raises(
        ValueError, match="File appears to be binary or contains invalid text encoding"
    ):
        assert _parse_attachment_file(file_attachment)


def test_chat_management_list(mock_dbus_service, capsys, default_namespace):
    mock_dbus_service.GetAllChatFromUser = lambda user_id: ChatList(
        [ChatEntry(created_at=str(datetime.now()))]
    ).structure()
    default_namespace.list = True

    ChatCommand(default_namespace).run()

    captured = capsys.readouterr()

    assert "Found a total of 1 chats:" in captured.out
    assert "0. Chat:" in captured.out


def test_chat_management_list_not_available(
    mock_dbus_service, capsys, default_namespace
):
    mock_dbus_service.GetAllChatFromUser = lambda user_id: ChatList([]).structure()

    default_namespace.list = True

    ChatCommand(default_namespace).run()

    captured = capsys.readouterr()

    assert "No chats available." in captured.out


def test_chat_management_delete(mock_dbus_service, capsys, default_namespace):
    mock_dbus_service.DeleteChatForUser = lambda user_id, name: None

    default_namespace.delete = "test"

    ChatCommand(default_namespace).run()

    captured = capsys.readouterr()

    assert "Chat test deleted successfully" in captured.out


def test_chat_management_delete_exception(mock_dbus_service, capsys, default_namespace):
    mock_dbus_service.DeleteChatForUser.side_effect = ChatNotFoundError(
        "chat not found"
    )

    default_namespace.delete = "test"
    assert ChatCommand(default_namespace).run() == 80
    captured = capsys.readouterr()

    assert "chat not found" in captured.err


def test_chat_management_delete_all(mock_dbus_service, capsys, default_namespace):
    mock_dbus_service.DeleteAllChatForUser = lambda user_id: None

    default_namespace.delete_all = True

    ChatCommand(default_namespace).run()

    captured = capsys.readouterr()

    assert "Deleted all chats successfully" in captured.out


def test_chat_management_delete_all_exception(
    mock_dbus_service, capsys, default_namespace
):
    mock_dbus_service.DeleteAllChatForUser.side_effect = ChatNotFoundError(
        "chat not found"
    )

    default_namespace.delete_all = True
    assert ChatCommand(default_namespace).run() == 80
    captured = capsys.readouterr()

    assert "chat not found" in captured.err


def test_create_chat_session(mock_dbus_service, base_chat_question_operation):
    mock_dbus_service.GetChatId = lambda user_id, name: "1"
    assert (
        base_chat_question_operation._create_chat_session("1", "test", "test2") == "1"
    )


def test_create_chat_session_exception(
    mock_dbus_service, default_namespace, base_chat_question_operation
):
    # This exception is swalloed because we will create a new chat for the user.
    mock_dbus_service.GetChatId.side_effect = ChatNotFoundError("no chat available")
    mock_dbus_service.CreateChat = lambda user_id, name, description: "1"
    assert (
        base_chat_question_operation._create_chat_session("1", "test", "test2") == "1"
    )


def test_interactive_mode_execution(default_namespace, default_kwargs):
    """Test interactive mode operation"""
    default_kwargs["args"] = default_namespace
    default_kwargs["user_proxy"].GetUserId.return_value = 1000
    default_kwargs["chat_proxy"].GetChatId.return_value = "1"
    default_kwargs["chat_proxy"].AskQuestion.return_value = Response("test").structure()
    with patch(
        "command_line_assistant.commands.chat.create_interactive_renderer"
    ) as mock_renderer:
        mock_renderer.return_value.render.side_effect = [None, StopInteractiveMode()]
        mock_renderer.return_value.output = "test"
        interactive_operation = InteractiveChatOperation(**default_kwargs)

    try:
        interactive_operation.execute()
    except Exception as e:
        pytest.fail(f"We got a failure in {interactive_operation} with stack: {str(e)}")


@pytest.mark.parametrize("exception", ((KeyboardInterrupt,), (EOFError,)))
def test_interactive_mode_sigkill_error(
    default_namespace, default_kwargs, monkeypatch, exception
):
    """Test interactive mode emulating KeyboardInterrupt question"""
    default_kwargs["args"] = default_namespace
    default_kwargs["user_proxy"].GetUserId.return_value = 1000
    default_kwargs["chat_proxy"].GetChatId.return_value = "1"
    default_kwargs["error_renderer"] = create_error_renderer()

    monkeypatch.setattr("builtins.input", mock.Mock(side_effect=exception))
    interactive_operation = InteractiveChatOperation(**default_kwargs)
    with pytest.raises(
        ChatCommandException,
        match="Detected keyboard interrupt. Stopping interactive mode.",
    ):
        interactive_operation.execute()


def test_interactive_mode_empty_question(default_namespace, default_kwargs, capsys):
    """Test interactive mode with empty question"""
    default_kwargs["args"] = default_namespace
    default_kwargs["user_proxy"].GetUserId.return_value = 1000
    default_kwargs["chat_proxy"].GetChatId.return_value = "1"
    default_kwargs["error_renderer"] = create_error_renderer()
    with patch(
        "command_line_assistant.commands.chat.create_interactive_renderer"
    ) as mock_renderer:
        interactive_operation = InteractiveChatOperation(**default_kwargs)
        mock_renderer.return_value.render.side_effect = [None, StopInteractiveMode()]
        mock_renderer.return_value.output = ""
        interactive_operation.execute()

        captured = capsys.readouterr()
        assert "Your question can't be empty" in captured.err


def test_interactive_chat_while_in_terminal_capture(default_namespace, default_kwargs):
    default_kwargs["args"] = default_namespace
    default_kwargs["error_renderer"] = create_error_renderer()
    with (
        NamedFileLock(name="terminal"),
        pytest.raises(
            ChatCommandException,
            match="Interactive chat mode is not available while terminal capture is active.",
        ),
    ):
        interactive_operation = InteractiveChatOperation(**default_kwargs)
        interactive_operation.execute()


@pytest.mark.parametrize(
    ("last_output_index", "expected_output"),
    [
        (-1, "last output"),
        (0, "first output"),
        (1, "middle output"),
    ],
)
def test_read_last_terminal_output(last_output_index, expected_output):
    """Test reading last terminal output"""
    with patch(
        "command_line_assistant.commands.chat.parse_terminal_output"
    ) as mock_parse:
        mock_parse.return_value = [
            {"command": "test", "output": "first output"},
            {"command": "test", "output": "middle output"},
            {"command": "test", "output": "last output"},
        ]
        result = _read_last_terminal_output(last_output_index)
        assert result == expected_output


def test_read_last_terminal_output_no_contents():
    with patch(
        "command_line_assistant.commands.chat.parse_terminal_output"
    ) as mock_parse:
        mock_parse.return_value = []
        result = _read_last_terminal_output(0)
        assert not result


def test_display_response(default_kwargs, capsys):
    """Test response display with legal notices"""
    base_chat_operation = BaseChatOperation(**default_kwargs)
    base_chat_operation._display_response("test response")

    captured = capsys.readouterr()
    # assert LEGAL_NOTICE in captured.out
    # assert "test response" in captured.out
    assert ALWAYS_LEGAL_MESSAGE in captured.out


def test_single_question_operation_with_exception(
    monkeypatch, default_kwargs, default_namespace
):
    default_namespace.query_string = "test"
    default_kwargs["args"] = default_namespace
    monkeypatch.setattr(
        chat, "_parse_attachment_file", mock.Mock(side_effect=ValueError("test"))
    )
    with pytest.raises(
        ChatCommandException, match="Failed to get a response from LLM. test"
    ):
        SingleQuestionOperation(**default_kwargs).execute()


def test_submit_question(mock_dbus_service, default_kwargs, capsys):
    mock_dbus_service.WriteHistory.return_value = None
    mock_dbus_service.AskQuestion.return_value = Response("test").structure()

    default_kwargs["text_renderer"] = create_text_renderer()

    chat_op = BaseChatOperation(**default_kwargs)
    result = chat_op._submit_question(
        "1b3fcbda-e875-11ef-abad-52b437312584",
        "1b3fcbda-e875-11ef-abad-52b437312584",
        "test",
        "",
        "",
        "",
        "",
        False,
    )
    assert result == "test"
    captured = capsys.readouterr()
    assert "Asking RHEL Lightspeed" in captured.out


def test_submit_question_no_spinner(mock_dbus_service, default_kwargs, capsys):
    mock_dbus_service.WriteHistory.return_value = None
    mock_dbus_service.AskQuestion.return_value = Response("test").structure()

    default_kwargs["text_renderer"] = create_text_renderer()

    chat_op = BaseChatOperation(**default_kwargs)
    result = chat_op._submit_question(
        "1b3fcbda-e875-11ef-abad-52b437312584",
        "1b3fcbda-e875-11ef-abad-52b437312584",
        "test",
        "",
        "",
        "",
        "",
        True,
    )
    assert result == "test"
    captured = capsys.readouterr()
    assert "Asking RHEL Lightspeed" not in captured.out


@pytest.mark.parametrize(
    ("question", "stdin", "attachment", "last_output"),
    (
        ("test " * 2048, "", "", ""),
        ("", "test " * 2048, "", ""),
        ("", "", "test " * 2048, ""),
        ("", "", "", "test " * 2048),
        # Combining two or more sources
        ("question " * 2048, "stdin " * 124, "", ""),
        ("question " * 2048, "stdin " * 124, "attachment" * 124, "last_output" * 124),
    ),
)
def test_trim_down_message_size(
    question,
    stdin,
    attachment,
    last_output,
    mock_dbus_service,
    default_kwargs,
    capsys,
    caplog,
):
    mock_dbus_service.WriteHistory.return_value = None
    mock_dbus_service.AskQuestion.return_value = Response("test").structure()

    default_kwargs["text_renderer"] = create_text_renderer()
    default_kwargs["warning_renderer"] = create_text_renderer()

    chat_op = BaseChatOperation(**default_kwargs)
    result = chat_op._submit_question(
        "1b3fcbda-e875-11ef-abad-52b437312584",
        "1b3fcbda-e875-11ef-abad-52b437312584",
        question,
        stdin,
        attachment,
        "",
        last_output,
        True,
    )
    assert result == "test"
    captured = capsys.readouterr()
    assert "The total size of your question and context" in captured.out
    assert "Final size of question after the limit 2048." in caplog.records[-3].message


def test_submit_question_history_disabled(
    mock_dbus_service, default_kwargs, capsys, caplog
):
    mock_dbus_service.WriteHistory.side_effect = HistoryNotEnabledError(
        "History is disabled"
    )
    mock_dbus_service.AskQuestion.return_value = Response("test").structure()

    default_kwargs["text_renderer"] = create_text_renderer()

    chat_op = BaseChatOperation(**default_kwargs)
    result = chat_op._submit_question(
        "1b3fcbda-e875-11ef-abad-52b437312584",
        "1b3fcbda-e875-11ef-abad-52b437312584",
        "test",
        "",
        "",
        "",
        "",
        True,
    )
    captured = capsys.readouterr()
    assert result == "test"
    assert "Asking RHEL Lightspeed" not in captured.out
    assert (
        "The history is disabled in the configuration file. Skipping the write to the history."
        in caplog.records[-2].message
    )


def test_interactive_mode_multiple_questions(default_kwargs, default_namespace):
    """Test interactive mode handling multiple questions"""
    default_kwargs["user_proxy"].GetUserId.return_value = 1000
    default_kwargs["chat_proxy"].GetChatId.return_value = "1"
    default_kwargs["chat_proxy"].AskQuestion.side_effect = [
        Response("response 1").structure(),
        Response("response 2").structure(),
    ]
    default_kwargs["args"] = default_namespace

    with patch(
        "command_line_assistant.commands.chat.create_interactive_renderer"
    ) as mock_renderer:
        mock_renderer.return_value.render.side_effect = [
            None,
            None,
            StopInteractiveMode(),
        ]
        mock_renderer.return_value.output = "test question"

        interactive_operation = InteractiveChatOperation(**default_kwargs)

        interactive_operation.execute()

        # Verify multiple questions were answered
        assert default_kwargs["chat_proxy"].AskQuestion.call_count == 2


def test_chat_operation_with_history_disabled(default_kwargs, capsys, caplog):
    """Test chat operation when history is disabled"""
    default_kwargs["history_proxy"].WriteHistory.side_effect = HistoryNotEnabledError(
        "History is disabled"
    )
    default_kwargs["chat_proxy"].AskQuestion.return_value = Response(
        "test response"
    ).structure()

    chat_op = BaseChatOperation(**default_kwargs)
    result = chat_op._submit_question(
        "test-user-id",
        "test-chat-id",
        "test question",
        "",
        "",
        "",
        "",
        True,
    )

    assert result == "test response"
    assert "The history is disabled in the configuration file" in caplog.text


def test_chat_command_with_invalid_args(default_namespace):
    """Test chat command with invalid/missing arguments"""
    # Remove query_string and stdin to simulate missing input
    default_namespace.query_string = None
    default_namespace.stdin = None
    default_namespace.attachment = None
    default_namespace.with_output = None

    command = ChatCommand(default_namespace)
    result = command.run()

    # TODO(r0x0d): Fix this later. It should exit with 1 and give the help message.
    assert result == 0  # Command should fail


@pytest.mark.parametrize(
    ("args", "expected"),
    (
        (
            {"query_string": "", "stdin": "", "with_output": ""},
            "Your query needs to have at least 2 characters. Either query or stdin are empty.",
        ),
        (
            {"query_string": "a", "stdin": "", "with_output": ""},
            "Your query needs to have at least 2 characters.",
        ),
        (
            {"query_string": "", "stdin": "a", "with_output": ""},
            "Your stdin input needs to have at least 2 characters.",
        ),
        (
            {"query_string": "aa", "stdin": "", "with_output": 1},
            "Adding context from terminal output is only allowed if terminal capture is active.",
        ),
    ),
)
def test_validate_query(args, expected, default_kwargs):
    default_kwargs["args"] = Namespace(**args)
    with pytest.raises(ChatCommandException, match=expected):
        SingleQuestionOperation(**default_kwargs).execute()
