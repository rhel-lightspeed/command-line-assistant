"""Simplified chat command implementation."""

import argparse
import logging
import platform
from argparse import Namespace
from dataclasses import dataclass
from io import TextIOWrapper
from typing import Optional

from command_line_assistant.dbus.exceptions import (
    ChatNotFoundError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.structures.chat import (
    AttachmentInput,
    ChatList,
    Question,
    Response,
    StdinInput,
    SystemInfo,
    TerminalInput,
)
from command_line_assistant.exceptions import ChatCommandException, StopInteractiveMode
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import (
    WriteOncePerSessionDecorator,
)
from command_line_assistant.terminal.parser import (
    find_output_by_index,
    parse_terminal_output,
)
from command_line_assistant.terminal.reader import TERMINAL_CAPTURE_FILE
from command_line_assistant.utils.benchmark import TimingLogger
from command_line_assistant.utils.cli import (
    CommandContext,
    argument,
    command,
)
from command_line_assistant.utils.dbus import DbusUtils
from command_line_assistant.utils.files import NamedFileLock, guess_mimetype
from command_line_assistant.utils.renderers import (
    RenderUtils,
    create_interactive_renderer,
    create_markdown_renderer,
    create_spinner_renderer,
    create_text_renderer,
    format_datetime,
    human_readable_size,
)

logger = logging.getLogger(__name__)

timing = TimingLogger(
    filtered_params=[
        "question",
        "stdin",
        "attachment",
        "attachment_mimetype",
        "last_output",
    ]
)

# Constants
MAX_QUESTION_SIZE: int = 32_000
LEGAL_NOTICE = (
    "This feature uses AI technology. Do not include any personal information or "
    "other sensitive information in your input. Interactions may be used to "
    "improve Red Hat's products or services."
)
ALWAYS_LEGAL_MESSAGE = "Always review AI-generated content prior to use."
DEFAULT_CHAT_DESCRIPTION = "Default Command Line Assistant Chat."
DEFAULT_CHAT_NAME = "default"


@dataclass
class InputSource:
    """Input source for the chat command.

    Parameters:
        question (str): The question to ask.
        stdin (str): The input from stdin.
        attachment (str): The attachment to use.
        attachment_mimetype (str): The mimetype of the attachment.
        terminal_output (str): The output from the terminal.
    """

    question: str
    stdin: str
    attachment: str
    attachment_mimetype: str
    terminal_output: str

    def get_input_source(self) -> str:
        """Determine and return the appropriate input source based on combination rules.

        Returns:
            str: The input source.
        """
        # All present - positional and file take precedence
        if all([self.question, self.stdin, self.attachment, self.terminal_output]):
            logger.debug(
                "Using positional query and file input. Stdin will be ignored."
            )
            return f"{self.question} {self.attachment}"

        # Positional + attachment + last output
        if self.question and self.attachment and self.terminal_output:
            logger.info(
                "Positional query, attachment and last output found. Using all of them at once."
            )
            return f"{self.question} {self.attachment} {self.terminal_output}"

        # Positional + last_output
        if self.question and self.terminal_output:
            logger.info("Positional query and last output found. Using them.")
            return f"{self.question} {self.terminal_output}"

        # Positional + file
        if self.question and self.attachment:
            logger.info("Positional query and attachment found. Using them.")
            return f"{self.question} {self.attachment}"

        # Stdin + file
        if self.stdin and self.attachment:
            logger.info("stdin and attachment found. Using them.")
            return f"{self.stdin} {self.attachment}"

        # Stdin + positional
        if self.stdin and self.question:
            logger.info("Positional query and stdin found. Using them.")
            return f"{self.question} {self.stdin}"

        # Single source - return first non-empty source
        logger.info(
            "Defaulting to use any of positional query, stdin, attachment or last output since no combinations where provided."
        )
        source = next(
            (
                src
                for src in [
                    self.question,
                    self.stdin,
                    self.attachment,
                    self.terminal_output,
                ]
                if src
            ),
            None,
        )

        if not source:
            logger.error("Couldn't find a match.")
            raise ValueError(
                "No input provided. Please provide input via file, stdin, or direct query."
            )

        return source


@command("chat", help="Command to ask a question to the LLM")
@argument(
    "query_string",
    nargs="?",
    help="The question that will be sent to the LLM",
    default="",
)
@argument(
    "-a",
    "--attachment",
    nargs="?",
    type=argparse.FileType("r"),
    help="File attachment to be read and sent alongside the query",
)
@argument(
    "-i", "--interactive", action="store_true", help="Start an interactive chat session"
)
@argument(
    "-w",
    "--with-output",
    nargs="?",
    type=int,
    help="Add output from terminal as context for the query. Use 1 to retrieve the latest output, 2 to and so on. First, enable the terminal capture with 'c shell --enable-capture' for this option to work.",
)
@argument("-l", "--list", action="store_true", help="List all chats")
@argument(
    "-d",
    "--delete",
    nargs="?",
    default="",
    help="Delete a chat session. Specify the chat session by its name.",
)
@argument("--delete-all", action="store_true", help="Delete all chats")
@argument("-n", "--name", nargs="?", help="Give a name to the chat session.")
@argument("--description", nargs="?", help="Give a description to the chat session.")
def chat_command(args: Namespace, context: CommandContext) -> int:
    """Main chat command implementation.

    This command allows users to interact with chat sessions, either by starting an interactive chat session,
    adding output from the terminal as context for the query, listing all chats, deleting a chat session,
    deleting all chats, or giving a name and description to the chat session.

    Args:
        args (Namespace): The command-line arguments.
        context (CommandContext): The command context.

    Returns:
        int: The exit code.
    """
    render = RenderUtils(args.plain)
    dbus = DbusUtils()

    user_id = dbus.user_proxy.GetUserId(context.effective_user_id)

    try:
        # Handle special arguments preprocessing
        if args.with_output:
            logger.debug(
                "Converting the index to a negative number in order to reverse search the output list."
            )
            logger.debug("Original index is %s", args.with_output)
            args.with_output = -abs(args.with_output)

        # Set default name and description
        name = args.name or DEFAULT_CHAT_NAME
        description = args.description or DEFAULT_CHAT_DESCRIPTION

        if not args.description and args.name:
            render.render_warning(
                "Chat description not provided. Using the default description: "
                f"'{DEFAULT_CHAT_DESCRIPTION}'. You can specify a custom description using the '--description' option."
            )

        if not args.name and args.description:
            render.render_warning(
                "Chat name not provided. Using the default name: "
                f"'{DEFAULT_CHAT_NAME}'. You can specify a custom name using the '--name' option."
            )

        # Handle different operations
        if args.list:
            return _list_chats(render, dbus, user_id)
        elif args.delete:
            return _delete_chat(render, dbus, user_id, args.delete)
        elif args.delete_all:
            return _delete_all_chats(render, dbus, user_id)
        elif args.interactive:
            # We pass down the args as there is many options we need to consult
            return _interactive_chat(
                render, dbus, context, args, user_id, name, description
            )
        else:
            # We pass down the args as there is many options we need to consult
            return _single_question(
                render, dbus, context, args, user_id, name, description
            )
    except ChatCommandException as e:
        logger.info("Failed to execute chat command: %s", str(e))
        render.render_error(str(e))
        return e.code


def _read_last_terminal_output(index: int) -> str:
    """Read the last terminal output by index.

    Args:
        index (int): The index of the terminal output to read.

    Returns:
        str: The contents of the terminal output.
    """
    logger.info("Reading terminal output.")
    contents = parse_terminal_output()

    if not contents:
        logger.info("No contents found during reading the terminal output.")
        return ""

    return find_output_by_index(index=index, output=contents)


def _parse_attachment_file(attachment: Optional[TextIOWrapper] = None) -> str:
    """Parse attachment file and read its contents.

    Args:
        attachment (Optional[TextIOWrapper]): The attachment file to parse.

    Returns:
        str: The contents of the attachment file.
    """
    if not attachment:
        return ""

    try:
        return attachment.read().strip()
    except UnicodeDecodeError as e:
        raise ValueError(
            "File appears to be binary or contains invalid text encoding"
        ) from e


def _create_chat_session(
    dbus: DbusUtils, user_id: str, name: str, description: str
) -> str:
    """Create a new chat session for a given conversation.

    Args:
        dbus (DbusUtils): The DbusUtils object.
        user_id (str): The user ID.
        name (str): The name of the chat.
        description (str): The description of the chat.

    Returns:
        str: The ID of the created chat session.
    """
    has_chat_id = None
    try:
        has_chat_id = dbus.chat_proxy.GetChatId(user_id, name)
    except ChatNotFoundError:
        # It's okay to swallow this exception as if there is no chat for
        # this user, we will create one.
        pass

    # To avoid doing this check inside the CreateChat method, let's do it
    # in here.
    if has_chat_id:
        return has_chat_id

    return dbus.chat_proxy.CreateChat(user_id, name, description)


def _display_response(response: str, plain: bool = False) -> None:
    """Display message to the terminal.

    Args:
        response (str): The response to display.
        plain (bool, optional): Whether to display in plain text. Defaults to False.
    """
    legal_renderer = create_text_renderer(
        decorators=[
            ColorDecorator(foreground="lightyellow"),
            WriteOncePerSessionDecorator(state_filename="legal"),
        ],
        plain=plain,
    )
    notice_renderer = create_text_renderer(
        decorators=[ColorDecorator(foreground="lightyellow")], plain=plain
    )
    markdown_renderer = create_markdown_renderer(plain=plain)

    legal_renderer.render(LEGAL_NOTICE)
    legal_renderer.render("─" * 72)
    print("")
    markdown_renderer.render(response)
    print("")
    legal_renderer.render("─" * 72)
    notice_renderer.render(ALWAYS_LEGAL_MESSAGE)


@timing.timeit
def _submit_question(
    dbus: DbusUtils,
    user_id: str,
    chat_id: str,
    message_input: Question,
    plain: bool,
) -> str:
    """Submit the question over dbus.

    Args:
        dbus (DbusUtils): The dbus utils object.
        user_id (str): The user id.
        chat_id (str): The chat id.
        message_input (Question): The question.
        plain (bool): Whether to render in plain text.

    Returns:
        str: The response.
    """
    spinner_renderer = create_spinner_renderer(
        message="Asking RHEL Lightspeed",
        plain=plain,
    )
    with spinner_renderer:
        response = _get_response(dbus, message_input, user_id)

    try:
        dbus.history_proxy.WriteHistory(
            chat_id, user_id, message_input.message, response
        )
    except HistoryNotEnabledError:
        logger.warning(
            "The history is disabled in the configuration file. Skipping the write to the history."
        )

    return response


def _trim_message_size(render: RenderUtils, question: str) -> str:
    """Trim the message size to fit within the maximum allowed size.

    Args:
        render (RenderUtils): The render object to display warnings.
        question (str): The question to be trimmed.

    Returns:
        str: The trimmed question.
    """
    question_length = len(question)
    final_question = question
    if question_length >= MAX_QUESTION_SIZE:
        readable_size = human_readable_size(question_length)
        max_question_size = human_readable_size(MAX_QUESTION_SIZE)
        render.render_warning(
            f"The total size of your question and context ({readable_size}) exceeds the limit of {max_question_size}. Trimming it down to fit in the expected size, you may lose some context."
        )
        logger.debug(
            "Total size of question (%s) exceeds defined limit of %s.",
            question_length,
            MAX_QUESTION_SIZE,
        )
        final_question = question[:MAX_QUESTION_SIZE]
        logger.debug("Final size of question after the limit %s.", question_length)

    return final_question


def _compose_message_input(
    render: RenderUtils, context: CommandContext, input_source: InputSource
) -> Question:
    """Compose the final message that will be sent to the API.

    Args:
        render (RenderUtils): The render utility.
        context (CommandContext): The command context.
        input_source (InputSource): The input source.

    Returns:
        Question: The composed message input.
    """
    final_question = _trim_message_size(render, input_source.get_input_source())
    message_input = Question(
        message=final_question,
        stdin=StdinInput(stdin=input_source.stdin),
        attachment=AttachmentInput(
            contents=input_source.attachment,
            mimetype=input_source.attachment_mimetype,
        ),
        terminal=TerminalInput(output=input_source.terminal_output),
        systeminfo=SystemInfo(
            os=context.os_release["name"],
            version=context.os_release["version_id"],
            arch=platform.machine(),
            id=context.os_release["id"],
        ),
    )

    return message_input


def _gather_input_sources(args: Namespace) -> InputSource:
    """Gather input sources from command-line arguments.

    Args:
        args (Namespace): The command-line arguments.

    Returns:
        InputSource: The gathered input sources.
    """
    terminal_output = ""
    if args.with_output:
        message = "Retrieving context from with-output parameter (index %s)"
        logger.debug(message, args.with_output)
        terminal_output = _read_last_terminal_output(args.with_output)

    attachment = _parse_attachment_file(args.attachment)
    attachment_mimetype = guess_mimetype(args.attachment)
    stdin = args.stdin.strip() if args.stdin else ""
    question = args.query_string.strip() if args.query_string else ""
    return InputSource(
        question, stdin, attachment, attachment_mimetype, terminal_output
    )


@timing.timeit
def _get_response(
    dbus: DbusUtils,
    message_input: Question,
    user_id: str,
) -> str:
    """Get the response from the chat session.

    Args:
        dbus (DbusUtils): The DbusUtils instance.
        message_input (Question): The message input.
        user_id (str): The user ID.

    Returns:
        str: The response message.
    """
    response = dbus.chat_proxy.AskQuestion(user_id, message_input.structure())
    return Response.from_structure(response).message


def _list_chats(render: RenderUtils, dbus: DbusUtils, user_id: str) -> int:
    """List all chats operation.

    Args:
        render (RenderUtils): The RenderUtils instance.
        dbus (DbusUtils): The DbusUtils instance.
        user_id (str): The user ID.

    Returns:
        int: The exit code.
    """
    all_chats = ChatList.from_structure(dbus.chat_proxy.GetAllChatFromUser(user_id))

    if not all_chats.chats:
        render.render_success("No chats available.")
        return 0

    render.render_success(f"Found a total of {len(all_chats.chats)} chats:")
    for index, chat in enumerate(all_chats.chats):
        created_at = format_datetime(chat.created_at)
        render.render_success(
            f"{index}. Chat: {chat.name} - {chat.description} (created at: {created_at})"
        )
    return 0


def _delete_chat(
    render: RenderUtils, dbus: DbusUtils, user_id: str, chat_name: str
) -> int:
    """Delete a specific chat operation.

    Args:
        render (RenderUtils): The RenderUtils instance.
        dbus (DbusUtils): The DbusUtils instance.
        user_id (str): The user ID.
        chat_name (str): The chat name.

    Returns:
        int: The exit code.
    """
    try:
        dbus.chat_proxy.DeleteChatForUser(user_id, chat_name)
        render.render_success(f"Chat {chat_name} deleted successfully.")
        return 0
    except ChatNotFoundError as e:
        raise ChatCommandException(f"Failed to delete requested chat {str(e)}") from e


def _delete_all_chats(render: RenderUtils, dbus: DbusUtils, user_id: str) -> int:
    """Delete all chats operation.

    Args:
        render (RenderUtils): The RenderUtils instance.
        dbus (DbusUtils): The DbusUtils instance.
        user_id (str): The user ID.

    Returns:
        int: The exit code.
    """
    try:
        dbus.chat_proxy.DeleteAllChatForUser(user_id)
        render.render_success("Deleted all chats successfully.")
        return 0
    except ChatNotFoundError as e:
        raise ChatCommandException(
            f"Failed to delete all requested chats {str(e)}"
        ) from e


def _interactive_chat(
    render: RenderUtils,
    dbus: DbusUtils,
    context: CommandContext,
    args: Namespace,
    user_id: str,
    name: str,
    description: str,
) -> int:
    """Interactive chat operation.

    Args:
        render (RenderUtils): The RenderUtils instance.
        dbus (DbusUtils): The DbusUtils instance.
        context (CommandContext): The CommandContext instance.
        args (Namespace): The Namespace instance.
        user_id (str): The user ID.
        name (str): The chat name.
        description (str): The chat description.

    Returns:
        int: The exit code.
    """
    terminal_file_lock = NamedFileLock(name="terminal")

    if terminal_file_lock.is_locked:
        raise ChatCommandException(
            f"Detected a terminal capture session running with pid '{terminal_file_lock.pid}'."
            " Interactive chat mode is not available while terminal capture is active, you must stop the previous one."
        )

    interactive_renderer = create_interactive_renderer()
    input_source = _gather_input_sources(args)
    chat_id = _create_chat_session(dbus, user_id, name, description)

    try:
        while True:
            interactive_renderer.render(">>> ")
            question = interactive_renderer.output
            if not question:
                render.render_error("Your question can't be empty. Please, try again.")
                continue

            input_source.question = question
            message_input = _compose_message_input(render, context, input_source)
            response = _submit_question(
                dbus=dbus,
                user_id=user_id,
                chat_id=chat_id,
                message_input=message_input,
                plain=args.plain,
            )
            _display_response(response, args.plain)
    except (KeyboardInterrupt, EOFError) as e:
        raise ChatCommandException(
            "Detected keyboard interrupt. Stopping interactive mode."
        ) from e
    except StopInteractiveMode:
        return 0


def _single_question(
    render: RenderUtils,
    dbus: DbusUtils,
    context: CommandContext,
    args: Namespace,
    user_id: str,
    name: str,
    description: str,
) -> int:
    """Single question operation.

    Args:
        render (RenderUtils): The RenderUtils instance.
        dbus (DbusUtils): The DbusUtils instance.
        context (CommandContext): The CommandContext instance.
        args (Namespace): The Namespace instance.
        user_id (str): The user ID.
        name (str): The chat name.
        description (str): The chat description.

    Returns:
        int: The exit code.
    """
    # Validate query
    is_query_invalid = _validate_query_composition(args)

    # In case we have any string in it, it means the query is invalid and we
    # raise an exception with the message returned.
    if is_query_invalid:
        raise ChatCommandException(is_query_invalid)

    input_source = _gather_input_sources(args)
    message_input = _compose_message_input(render, context, input_source)

    try:
        chat_id = _create_chat_session(dbus, user_id, name, description)
        response = _submit_question(
            dbus=dbus,
            user_id=user_id,
            chat_id=chat_id,
            message_input=message_input,
            plain=args.plain,
        )

        _display_response(response, args.plain)
        return 0
    except ValueError as e:
        message = f"Failed to get a response from LLM. {str(e)}"
        raise ChatCommandException(message) from e


def _validate_query_composition(args: Namespace) -> Optional[str]:
    """Valid if the query compostion is valid or not.

    Args:
        args (Namespace): The Namespace instance.

    Returns:
        Optional[str]: In case the query is not valid by any means in the validation.
    """
    if not args.query_string and not args.stdin:
        logger.debug("Both query_string and stdin are empty.")
        return "Your query needs to have at least 2 characters. Either query or stdin are empty."

    if args.query_string and len(args.query_string.strip()) <= 1:
        logger.debug(
            "Query string has only 1 or 0 characters after stripping: '%s'",
            args.query_string,
        )
        return "Your query needs to have at least 2 characters."

    if args.stdin and len(args.stdin.strip()) <= 1:
        logger.debug(
            "Stdin has only 1 or 0 characters after stripping: '%s'",
            args.stdin,
        )
        return "Your stdin input needs to have at least 2 characters."

    if args.with_output and not TERMINAL_CAPTURE_FILE.exists():
        return "Adding context from terminal output is only allowed if terminal capture is active."

    return None
