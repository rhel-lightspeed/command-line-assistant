"""Module to handle the chat command."""

import argparse
import logging
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
    TerminalInput,
)
from command_line_assistant.exceptions import ChatCommandException, StopInteractiveMode
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import (
    WriteOnceDecorator,
)
from command_line_assistant.rendering.renders.interactive import InteractiveRenderer
from command_line_assistant.rendering.renders.spinner import SpinnerRenderer
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.terminal.parser import (
    clean_parsed_text,
    find_output_by_index,
    parse_terminal_output,
)
from command_line_assistant.utils.cli import (
    CommandContext,
    SubParsersAction,
)
from command_line_assistant.utils.files import guess_mimetype
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_interactive_renderer,
    create_spinner_renderer,
    create_text_renderer,
)

logger = logging.getLogger(__name__)

#: Legal notice that we need to output once per user
LEGAL_NOTICE = (
    "This feature uses AI technology. Do not include personal information or "
    "other sensitive information in your input. Interactions may be used to "
    "improve Red Hat's products or services."
)
#: Always good to have legal message.
ALWAYS_LEGAL_MESSAGE = "Always review AI generated content prior to use."


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
        logger.info(
            "No contents found during reading the terminal output. Returning empty string."
        )
        return ""

    logger.info("Finding output by index, if any.")
    last_output = find_output_by_index(index=index, output=contents)
    return clean_parsed_text(last_output)


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


def _get_input_source(query: str, stdin: str, attachment: str, last_output: str) -> str:
    """
    Determine and return the appropriate input source based on combination rules.

    Arguments:
        query (str): The question to be asked
        stdin (str): The input redirect via stdin
        attachment (str): The attachment contents
        attachment_mimetype (str): The mimetype of the attachment
        last_output (str): The last out read from the terminal

    Warning:
        This is set to be deprecated in the future when we normalize the API
        backend to accept the context and works with it.

    Rules:
    1. Positional query only -> use positional query
    2. Stdin query only -> use stdin query
    3. File query only -> use file query
    4. Stdin + positional query -> combine as "{positional_query} {stdin}"
    5. Stdin + file query -> combine as "{stdin} {file_query}"
    6. Positional + file query -> combine as "{positional_query} {file_query}"
    7. Positional + last output -> combine as "{positional_query} {last_output}"
    8. Positional + attachment + last output -> combine as "{positional_query} {attachment} {last_output}"
    99. All three sources -> use only positional and file as "{positional_query} {file_query}"

    Raises:
        ValueError: If no input source is provided

    Returns:
        str: The query string from the selected input source(s)
    """
    # Rule 99: All present - positional and file take precedence
    if all([query, stdin, attachment, last_output]):
        logger.debug("Using positional query and file input. Stdin will be ignored.")
        return f"{query} {attachment}"

    # Rule 8: positional + attachment + last output
    if query and attachment and last_output:
        logger.info(
            "Positional query, attachment and last output found. Using all of them at once."
        )
        return f"{query} {attachment} {last_output}"

    # Rule 7: positional + last_output
    if query and last_output:
        logger.info("Positional query and last output found. Using them.")
        return f"{query} {last_output}"

    # Rule 6: Positional + file
    if query and attachment:
        logger.info("Positional query and attachment found. Using them.")
        return f"{query} {attachment}"

    # Rule 5: Stdin + file
    if stdin and attachment:
        logger.info("stdin and attachment found. Using them.")
        return f"{stdin} {attachment}"

    # Rule 4: Stdin + positional
    if stdin and query:
        logger.info("Positional query and stidn found. Using them.")
        return f"{query} {stdin}"

    # Rules 1-3: Single source - return first non-empty source
    logger.info(
        "Defaulting to use any of positional query, stdin, attachment or last output since no combinations where provided."
    )
    source = next(
        (src for src in [query, stdin, attachment, last_output] if src),
        None,
    )

    if source:
        return source

    logger.error("Couldn't find a match.")
    raise ValueError(
        "No input provided. Please provide input via file, stdin, or direct query."
    )


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
        "last_output": ChatOperationType.SINGLE_QUESTION,
    }


class BaseChatOperation(BaseOperation):
    """Base class for handling chat operations

    Attributes:
        spinner_renderer (SpinnerRenderer): The instance of a spinner renderer
        legal_renderer (TextRenderer): Instance of text renderer to show legal message
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
        )
        self.legal_renderer: TextRenderer = create_text_renderer(
            decorators=[
                ColorDecorator(foreground="lightyellow"),
                WriteOnceDecorator(state_filename="legal"),
            ]
        )
        self.notice_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator(foreground="lightyellow")]
        )
        self.interactive_renderer: InteractiveRenderer = create_interactive_renderer()

    def _display_response(self, response: str) -> None:
        """Internal method to display message to the terminal

        Arguments:
            response(str): The message to be displayed
        """
        self.legal_renderer.render(LEGAL_NOTICE)
        self.text_renderer.render(response)
        self.notice_renderer.render(ALWAYS_LEGAL_MESSAGE)

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
        final_question = _get_input_source(question, stdin, attachment, last_output)
        with self.spinner_renderer:
            response = self._get_response(
                user_id,
                final_question,
                stdin,
                attachment,
                attachment_mimetype,
                last_output,
            )
            self.history_proxy.WriteHistory(chat_id, user_id, final_question, response)
            return response

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
            self.text_renderer.render(
                f"{index}. Chat: {chat.name} - {chat.description} (created at: {chat.created_at})"
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
        except StopInteractiveMode as e:
            raise ChatCommandException(str(e)) from e


@ChatOperationFactory.register(ChatOperationType.SINGLE_QUESTION)
class SingleQuestionOperation(BaseChatOperation):
    """Class that holds the single question ask operation"""

    def execute(self) -> None:
        """Default method to execute the operation"""
        try:
            last_terminal_output = _read_last_terminal_output(self.args.last_output)
            attachment = _parse_attachment_file(self.args.attachment)
            attachment_mimetype = guess_mimetype(self.args.attachment)
            stdin = self.args.stdin.strip()
            question = self.args.query_string.strip()

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
        error_renderer = create_error_renderer()
        operation_factory = ChatOperationFactory()
        try:
            operation = operation_factory.create_operation(
                self._args,
                self._context,
                text_renderer=create_text_renderer(
                    decorators=[ColorDecorator(foreground="green")],
                ),
                error_renderer=error_renderer,
            )
            if operation:
                operation.execute()
            return 0
        except ChatCommandException as e:
            error_renderer.render(str(e))
            return 1


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
        "query_string", nargs="?", help="The question that will be sent to the LLM"
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
        help="Start interactive chat session",
    )
    question_group.add_argument(
        "-o",
        "--with-output",
        nargs="?",
        type=int,
        # In case nothing is supplied
        const=1,
        default=1,
        help="Read last output from terminal. Default to last entry collected.",
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
        help="Delete a chat session",
    )
    chat_arguments.add_argument(
        "--delete-all", action="store_true", help="Delete all chats"
    )
    chat_arguments.add_argument(
        "-n",
        "--name",
        nargs="?",
        help="Give a name to the chat session",
        default="default",
    )
    chat_arguments.add_argument(
        "--description",
        nargs="?",
        help="Give a description to the chat session",
        default="Default Command Line Assistant Chat.",
    )

    chat_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> ChatCommand:
    """Internal command factory to create the command class

    Arguments:
        args (Namespace): The arguments processed with argparse.

    Returns:
        QueryCommand: Return an instance of class
    """
    return ChatCommand(args)
