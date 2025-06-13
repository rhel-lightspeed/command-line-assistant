"""Module to handle the chat command."""

import argparse
import logging
import os
import platform
from argparse import Namespace
from enum import auto
from io import TextIOWrapper
from typing import ClassVar, Optional

from command_line_assistant.commands.base import (
    BaseCLICommand,
    BaseOperation,
    CommandOperationFactory,
    CommandOperationType,
)
from command_line_assistant.dbus.exceptions import (
    ChatNotFoundError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.interfaces.chat import ChatInterface
from command_line_assistant.dbus.interfaces.history import HistoryInterface
from command_line_assistant.dbus.interfaces.user import UserInterface
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
from command_line_assistant.rendering.renders.interactive import InteractiveRenderer
from command_line_assistant.rendering.renders.markdown import MarkdownRenderer
from command_line_assistant.rendering.renders.spinner import SpinnerRenderer
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.terminal.parser import (
    find_output_by_index,
    parse_terminal_output,
)
from command_line_assistant.terminal.reader import TERMINAL_CAPTURE_FILE
from command_line_assistant.utils.benchmark import TimingLogger
from command_line_assistant.utils.cli import (
    CommandContext,
    SubParsersAction,
)
from command_line_assistant.utils.environment import get_xdg_state_path
from command_line_assistant.utils.files import (
    NamedFileLock,
    create_folder,
    guess_mimetype,
    write_file,
)
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_interactive_renderer,
    create_markdown_renderer,
    create_spinner_renderer,
    create_text_renderer,
    create_warning_renderer,
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

#: Max input size we want to allow to be submitted to the backend. This
#: corresponds to 32KB (32000 bytes)
MAX_QUESTION_SIZE: int = 32_000

#: Legal notice that we need to output once per user
LEGAL_NOTICE = (
    "This feature uses AI technology. Do not include any personal information or "
    "other sensitive information in your input. Interactions may be used to "
    "improve Red Hat's products or services."
)
#: Always good to have legal message.
ALWAYS_LEGAL_MESSAGE = "Always review AI-generated content prior to use."

#: Default chat description when none is given
DEFAULT_CHAT_DESCRIPTION = "Default Command Line Assistant Chat."

#: Default chat name when none is given
DEFAULT_CHAT_NAME = "default"


def _read_last_terminal_output(index: int) -> str:
    """Internal function to handle reading the last terminal output.

    Arguments:
        index (int): The index to grab the output from the list

    Returns:
        str: The data read or an empty string
    """
    logger.info("Reading terminal output.")
    contents = parse_terminal_output()

    if not contents:
        logger.info("No contents found during reading the terminal output.")
        return ""

    last_output = find_output_by_index(index=index, output=contents)
    return last_output


def _parse_attachment_file(attachment: Optional[TextIOWrapper] = None) -> str:
    """Parse the attachment file and read its contents.

    Arguments:
        attachment (Optional[TextIOWrapper], optional): The attachment that will be parsed

    Returns:
        str: Either the str read or None.
    """
    if not attachment:
        return ""

    try:
        return attachment.read().strip()
    except UnicodeDecodeError as e:
        raise ValueError(
            "File appears to be binary or contains invalid text encoding"
        ) from e


def _handle_legal_message() -> bool:
    """Handle legal message screen output

    Returns:
        bool: True if the legal message was handled successfully, False
        otherwise.
    """
    state_file = get_xdg_state_path() / "legal"
    parent_pid = str(os.getppid())

    if state_file.exists():
        if state_file.read_text() == parent_pid:
            logger.info(
                "The state file already exists. Skipping writting it a second time."
            )
            return False

    create_folder(state_file.parent, parents=True)
    # Write state file
    write_file(parent_pid, state_file)
    return True


class ChatOperationType(CommandOperationType):
    """Enum to control the operations for the command"""

    LIST_CHATS = auto()
    DELETE_CHAT = auto()
    DELETE_ALL_CHATS = auto()
    INTERACTIVE_CHAT = auto()
    SINGLE_QUESTION = auto()


class ChatOperationFactory(CommandOperationFactory):
    """Factory for creating shell operations with decorator-based registration"""

    # Mapping of CLI arguments to operation types
    _arg_to_operation: ClassVar[dict[str, CommandOperationType]] = {
        "list": ChatOperationType.LIST_CHATS,
        "delete": ChatOperationType.DELETE_CHAT,
        "delete_all": ChatOperationType.DELETE_ALL_CHATS,
        "interactive": ChatOperationType.INTERACTIVE_CHAT,
        "query_string": ChatOperationType.SINGLE_QUESTION,
        "stdin": ChatOperationType.SINGLE_QUESTION,
        "attachment": ChatOperationType.SINGLE_QUESTION,
        "with_output": ChatOperationType.SINGLE_QUESTION,
    }


class BaseChatOperation(BaseOperation):
    """Base class for handling chat operations

    Attributes:
        spinner_renderer (SpinnerRenderer): The instance of a spinner renderer
        notice_renderer (TextRenderer): Instance of text renderer to show notice message
        interactive_renderer (InteractiveRenderer): Instance of interactive renderer to handle interactive mode
    """

    def __init__(
        self,
        text_renderer: TextRenderer,
        warning_renderer: TextRenderer,
        error_renderer: TextRenderer,
        args: Namespace,
        context: CommandContext,
        chat_proxy: ChatInterface,
        history_proxy: HistoryInterface,
        user_proxy: UserInterface,
    ) -> None:
        """Constructor of the class.

        Arguments:
            text_renderer (TextRenderer): Instance of text renderer class
            warning_renderer (TextRenderer): Instance of text renderer class
            error_renderer (TextRenderer): Instance of text renderer class
            args (Namespace): The arguments from CLI
            context (CommandContext): Context for the commands
            chat_proxy (ChatInterface): The proxy object for dbus chat
            history_proxy (HistoryInterface): The proxy object for dbus history
            user_proxy (HistoryInterface): The proxy object for dbus user
        """
        super().__init__(
            text_renderer,
            warning_renderer,
            error_renderer,
            args,
            context,
            chat_proxy,
            history_proxy,
            user_proxy,
        )
        self.spinner_renderer: SpinnerRenderer = create_spinner_renderer(
            message="Asking RHEL Lightspeed",
            plain=hasattr(args, "plain") and args.plain,
        )
        self.notice_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator(foreground="lightyellow")],
            plain=hasattr(args, "plain") and args.plain,
        )
        self.interactive_renderer: InteractiveRenderer = create_interactive_renderer()
        self.markdown_renderer: MarkdownRenderer = create_markdown_renderer(
            plain=hasattr(args, "plain") and args.plain
        )

    def _display_response(self, response: str) -> None:
        """Internal method to display message to the terminal

        Arguments:
            response(str): The message to be displayed
        """
        if _handle_legal_message():
            self.notice_renderer.render(LEGAL_NOTICE)
            self.text_renderer.render("─" * 72)
            print("")

        self.markdown_renderer.render(response)
        print("")
        self.text_renderer.render("─" * 72)
        self.notice_renderer.render(ALWAYS_LEGAL_MESSAGE)

    @timing.timeit
    def _submit_question(
        self,
        user_id: str,
        chat_id: str,
        question: str,
        stdin: str,
        attachment: str,
        attachment_mimetype: str,
        last_output: str,
    ) -> str:
        """Submit the question over dbus.

        Arguments:
            user_id (str): The unique identifier for the user
            chat_id (str): The unique identifier for the chat
            question (str): The question to be asked
            stdin (str): The input redirect via stdin
            attachment (str): The attachment contents
            attachment_mimetype (str): The mimetype of the attachment
            last_output (str): The last out read from the terminal

        Returns:
            str: The response from the backend server
        """
        response = None

        sources = self._validate_input_sources_max_size(
            question, stdin, " ".join(attachment.split()[::-1]), last_output
        )

        with self.spinner_renderer:
            response = self._get_response(
                user_id=user_id,
                attachment_mimetype=attachment_mimetype,
                **sources,
            )
        try:
            self.history_proxy.WriteHistory(chat_id, user_id, question, response)
        except HistoryNotEnabledError:
            logger.warning(
                "The history is disabled in the configuration file. Skipping the write to the history."
            )

        return response

    def _validate_input_sources_max_size(
        self, question: str, stdin: str, attachment: str, last_output: str
    ):
        """Validate the input sources and trim them down to fit the maximum size.

        Arguments:
            question (str): The question to be asked
            stdin (str): The input redirect via stdin
            attachment (str): The attachment contents
            last_output (str): The last out read from the terminal

        Returns:
            dict: A dictionary with the sources and their values, trimmed to fit the maximum size.
        """
        sources = {
            "question": question,
            "stdin": stdin,
            "attachment": attachment,
            "last_output": last_output,
        }

        for source, value in sources.items():
            if len(value) <= MAX_QUESTION_SIZE:
                continue

            # If the value is larger than the maximum size, we need to trim it down
            readable_size = human_readable_size(len(value))
            max_question_size = human_readable_size(MAX_QUESTION_SIZE)
            self.warning_renderer.render(
                f"The total size of your input '{source}' ({readable_size}) exceeds the limit of {max_question_size}. "
                "Trimming it down to fit in the expected size, you may lose some context."
            )
            logger.debug(
                "Size of input (%s) exceeds defined limit of %s.",
                source,
                MAX_QUESTION_SIZE,
            )
            sources[source] = value[:MAX_QUESTION_SIZE]
            logger.debug("Final size of input after the limit %s.", len(source))

        return sources

    @timing.timeit
    def _get_response(
        self,
        user_id: str,
        question: str,
        stdin: str,
        attachment: str,
        attachment_mimetype: str,
        last_output: str,
    ) -> str:
        """Get the response from the chat session.

        Arguments:
            user_id (str): The user identifier
            chat_id (str): The chat session identifier
            question (str): The question to be asked
            stdin (str): The input redirect via stdin
            attachment (str): The attachment contents
            attachment_mimetype (str): The mimetype of the attachment
            last_output (str): The last out read from the terminal

        Returns:
            str: The response from the chat session
        """
        message_input = Question(
            message=question,
            stdin=StdinInput(stdin=stdin),
            attachment=AttachmentInput(
                contents=attachment, mimetype=attachment_mimetype
            ),
            terminal=TerminalInput(output=last_output),
            systeminfo=SystemInfo(
                os=self.context.os_release["name"],
                version=self.context.os_release["version_id"],
                arch=platform.machine(),
                id=self.context.os_release["id"],
            ),
        )
        response = self.chat_proxy.AskQuestion(
            user_id,
            message_input.structure(),
        )

        return Response.from_structure(response).message

    def _create_chat_session(self, user_id: str, name: str, description: str) -> str:
        """Create a new chat session for a given conversation.

        Arguments:
            user_id (str): The user identifier
            name (str): The name of the chat
            description (str): The description of the chat

        Returns:
            str: The identifier of the chat session.
        """
        has_chat_id = None
        try:
            has_chat_id = self.chat_proxy.GetChatId(user_id, name)
        except ChatNotFoundError:
            # It's okay to swallow this exception as if there is no chat for
            # this user, we will create one.
            pass

        # To avoid doing this check inside the CreateChat method, let's do it
        # in here.
        if has_chat_id:
            return has_chat_id

        return self.chat_proxy.CreateChat(
            user_id,
            name,
            description,
        )


@ChatOperationFactory.register(ChatOperationType.LIST_CHATS)
class ListChatsOperation(BaseChatOperation):
    """Class that holds the list operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
        all_chats = ChatList.from_structure(self.chat_proxy.GetAllChatFromUser(user_id))
        if not all_chats.chats:
            self.text_renderer.render("No chats available.")

        self.text_renderer.render(f"Found a total of {len(all_chats.chats)} chats:")
        for index, chat in enumerate(all_chats.chats):
            created_at = format_datetime(chat.created_at)
            self.text_renderer.render(
                f"{index}. Chat: {chat.name} - {chat.description} (created at: {created_at})"
            )


@ChatOperationFactory.register(ChatOperationType.DELETE_CHAT)
class DeleteChatOperation(BaseChatOperation):
    """Class that holds the delete operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        try:
            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            self.chat_proxy.DeleteChatForUser(user_id, self.args.delete)
            self.text_renderer.render(f"Chat {self.args.delete} deleted successfully.")
        except ChatNotFoundError as e:
            raise ChatCommandException(
                f"Failed to delete requested chat {str(e)}"
            ) from e


@ChatOperationFactory.register(ChatOperationType.DELETE_ALL_CHATS)
class DeleteAllChatsOperation(BaseChatOperation):
    """Class that holds the delete all operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        try:
            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            self.chat_proxy.DeleteAllChatForUser(user_id)
            self.text_renderer.render("Deleted all chats successfully.")
        except ChatNotFoundError as e:
            raise ChatCommandException(
                f"Failed to delete all requested chats {str(e)}"
            ) from e


@ChatOperationFactory.register(ChatOperationType.INTERACTIVE_CHAT)
class InteractiveChatOperation(BaseChatOperation):
    """Class that initiates the interactive mode"""

    def execute(self) -> None:
        """Default method to execute the operation"""

        terminal_file_lock = NamedFileLock(name="terminal")

        if terminal_file_lock.is_locked:
            raise ChatCommandException(
                f"Detected a terminal capture session running with pid '{terminal_file_lock.pid}'."
                " Interactive chat mode is not available while terminal capture is active, you must stop the previous one."
            )

        try:
            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            chat_id = self._create_chat_session(
                user_id, self.args.name, self.args.description
            )
            attachment = _parse_attachment_file(self.args.attachment)
            attachment_mimetype = guess_mimetype(self.args.attachment)
            stdin = self.args.stdin

            while True:
                self.interactive_renderer.render(">>> ")
                question = self.interactive_renderer.output
                if not question:
                    self.error_renderer.render(
                        "Your question can't be empty. Please, try again."
                    )
                    continue
                response = self._submit_question(
                    user_id=user_id,
                    chat_id=chat_id,
                    question=question,
                    stdin=stdin,
                    attachment=attachment,
                    attachment_mimetype=attachment_mimetype,
                    # For now, we won't deal with last output in interactive mode.
                    last_output="",
                )
                self._display_response(response)
        except (KeyboardInterrupt, EOFError) as e:
            raise ChatCommandException(
                "Detected keyboard interrupt. Stopping interactive mode."
            ) from e
        except StopInteractiveMode:
            return


@ChatOperationFactory.register(ChatOperationType.SINGLE_QUESTION)
class SingleQuestionOperation(BaseChatOperation):
    """Class that holds the single question ask operation"""

    def _validate_query(self):
        """Helper function to validate query.

        Raises:
            ChatCommandException: In case the query has invalid sizing (less than 1 character).
        """
        # If both are empty, raise exception
        if not self.args.query_string and not self.args.stdin:
            logger.debug("Both query_string and stdin are empty.")
            raise ChatCommandException(
                "Your query needs to have at least 2 characters. Either query or stdin are empty."
            )

        # If query_string has content but is too short
        if self.args.query_string and len(self.args.query_string.strip()) <= 1:
            logger.debug(
                "Query string has only 1 or 0 characters after stripping: '%s'",
                self.args.query_string,
            )
            raise ChatCommandException(
                "Your query needs to have at least 2 characters."
            )

        # If stdin has content but is too short
        if self.args.stdin and len(self.args.stdin.strip()) <= 1:
            logger.debug(
                "Stdin has only 1 or 0 characters after stripping: '%s'",
                self.args.stdin,
            )
            raise ChatCommandException(
                "Your stdin input needs to have at least 2 characters."
            )

        # If the user tries to do "c -w 1" or "c -w 1 "help me figure this out"
        # and there is no terminal capture log file, we just error out.
        if self.args.with_output and not TERMINAL_CAPTURE_FILE.exists():
            raise ChatCommandException(
                "Adding context from terminal output is only allowed if terminal capture is active."
            )

    @timing.timeit
    def execute(self) -> None:
        """Default method to execute the operation"""

        self._validate_query()

        try:
            last_terminal_output = ""
            if self.args.with_output:
                logger.debug(
                    "Retrieving context from with-output parameter (index %s)",
                    self.args.with_output,
                )
                last_terminal_output = _read_last_terminal_output(self.args.with_output)

            attachment = _parse_attachment_file(self.args.attachment)
            attachment_mimetype = guess_mimetype(self.args.attachment)
            stdin = self.args.stdin.strip() if self.args.stdin else ""
            question = self.args.query_string.strip() if self.args.query_string else ""

            user_id = self.user_proxy.GetUserId(self.context.effective_user_id)
            chat_id = self._create_chat_session(
                user_id, self.args.name, self.args.description
            )
            response = self._submit_question(
                user_id=user_id,
                chat_id=chat_id,
                question=question,
                stdin=stdin,
                attachment=attachment,
                attachment_mimetype=attachment_mimetype,
                last_output=last_terminal_output,
            )

            self._display_response(response)
        except ValueError as e:
            raise ChatCommandException(
                f"Failed to get a response from LLM. {str(e)}"
            ) from e


class ChatCommand(BaseCLICommand):
    """Class that represents the chat command."""

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Status code of the execution
        """
        error_renderer = create_error_renderer(
            plain=hasattr(self._args, "plain") and self._args.plain
        )
        operation_factory = ChatOperationFactory()
        try:
            operation = operation_factory.create_operation(
                self._args,
                self._context,
                text_renderer=create_text_renderer(
                    decorators=[ColorDecorator()],
                    plain=hasattr(self._args, "plain") and self._args.plain,
                ),
                error_renderer=error_renderer,
            )

            if operation:
                operation.execute()
            return 0
        except ChatCommandException as e:
            logger.info("Failed to execute chat command: %s", str(e))
            error_renderer.render(str(e))
            return e.code


def register_subcommand(parser: SubParsersAction) -> None:
    """
    Register this command to argparse so it's available for the root parser.

    Arguments:
        parser (SubParsersAction): Root parser to register command-specific arguments
    """
    chat_parser = parser.add_parser(
        "chat",
        help="Command to ask a question to the LLM.",
    )

    question_group = chat_parser.add_argument_group("Question Options")
    # Positional argument, required only if no optional arguments are provided
    question_group.add_argument(
        "query_string",
        nargs="?",
        help="The question that will be sent to the LLM",
        default="",
    )
    question_group.add_argument(
        "-a",
        "--attachment",
        nargs="?",
        type=argparse.FileType("r"),
        help="File attachment to be read and sent alongside the query",
    )
    question_group.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Start an interactive chat session",
    )
    question_group.add_argument(
        "-w",
        "--with-output",
        nargs="?",
        type=int,
        help=(
            "Add output from terminal as context for the query. Use 1 to retrieve "
            "the latest output, 2 to and so on. First, enable the terminal "
            "capture with 'c shell --enable-capture' for this option to work."
        ),
    )

    chat_arguments = chat_parser.add_argument_group("Chat Options")
    chat_arguments.add_argument(
        "-l", "--list", action="store_true", help="List all chats"
    )
    chat_arguments.add_argument(
        "-d",
        "--delete",
        nargs="?",
        default="",
        help="Delete a chat session. Specify the chat session by its name.",
    )
    chat_arguments.add_argument(
        "--delete-all", action="store_true", help="Delete all chats"
    )
    chat_arguments.add_argument(
        "-n",
        "--name",
        nargs="?",
        help="Give a name to the chat session. Parameter has to be used together with sending a query. Otherwise has no effect.",
    )
    chat_arguments.add_argument(
        "--description",
        nargs="?",
        help="Give a description to the chat session. Parameter has to be used together with sending a query. Otherwise has no effect.",
    )

    chat_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> ChatCommand:
    """Internal command factory to create the command class

    Arguments:
        args (Namespace): The arguments processed with argparse.

    Returns:
        ChatCommand: Return an instance of class
    """
    if args.with_output:
        logger.debug(
            "Converting the index to a negative number in order to reverse search the output list."
        )
        logger.debug("Original index is %s", args.with_output)
        args.with_output = -abs(args.with_output)

    warning_renderer = create_warning_renderer()

    # Overriding the default description in case the user has not given us any.
    # We don't log this as warning to avoid spamming the user terminal with
    # this message.
    if not args.description and not args.name:
        args.description = DEFAULT_CHAT_DESCRIPTION
        args.name = DEFAULT_CHAT_NAME
        logger.debug("No name or description provided. Using default values.")

    if not args.description and args.name:
        args.description = DEFAULT_CHAT_DESCRIPTION
        warning_renderer.render(
            "Chat description not provided. Using the default description: "
            f"'{DEFAULT_CHAT_DESCRIPTION}'. You can specify a custom description using the '--description' option."
        )

    if not args.name and args.description:
        args.name = DEFAULT_CHAT_NAME
        warning_renderer.render(
            "Chat name not provided. Using the default name: "
            f"'{DEFAULT_CHAT_NAME}'. You can specify a custom name using the '--name' option."
        )

    return ChatCommand(args)
