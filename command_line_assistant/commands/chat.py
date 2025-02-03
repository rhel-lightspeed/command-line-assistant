"""Module to handle the chat command."""

import argparse
from argparse import Namespace
from io import TextIOWrapper
from typing import Optional

from command_line_assistant.dbus.constants import (
    CHAT_IDENTIFIER,
    HISTORY_IDENTIFIER,
    USER_IDENTIFIER,
)
from command_line_assistant.dbus.exceptions import (
    ChatNotFoundError,
    CorruptedHistoryError,
    MissingHistoryFileError,
    RequestFailedError,
)
from command_line_assistant.dbus.structures.chat import (
    AttachmentInput,
    ChatList,
    Question,
    Response,
    StdinInput,
)
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.text import (
    EmojiDecorator,
    WriteOnceDecorator,
)
from command_line_assistant.rendering.renders.spinner import SpinnerRenderer
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import BaseCLICommand, SubParsersAction
from command_line_assistant.utils.files import (
    guess_mimetype,
)
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_spinner_renderer,
    create_text_renderer,
    create_warning_renderer,
)

#: Legal notice that we need to output once per user
LEGAL_NOTICE = (
    "This feature uses AI technology. Do not include personal information or "
    "other sensitive information in your input. Interactions may be used to "
    "improve Red Hat's products or services."
)
#: Always good to have legal message.
ALWAYS_LEGAL_MESSAGE = "Always review AI generated content prior to use."


def _parse_attachment_file(attachment: Optional[TextIOWrapper] = None) -> str:
    """Parse the attachment file and read its contents.

    Args:
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


class ChatCommand(BaseCLICommand):
    """Class that represents the chat command."""

    def __init__(
        self,
        args: Namespace,
    ) -> None:
        """Constructor of the class.

        Args:
            args (Namespace): The argparse namespace object
        """
        self._args = args
        self._query = args.query_string.strip() if args.query_string else ""
        self._stdin = args.stdin.strip() if args.stdin else ""

        # Initialize it as None before we read and manipulate the rest.
        self._attachment = _parse_attachment_file(args.attachment)
        self._attachment_mimetype = guess_mimetype(args.attachment)

        self._spinner_renderer: SpinnerRenderer = create_spinner_renderer(
            message="Requesting knowledge from AI",
            decorators=[EmojiDecorator(emoji="U+1F916")],
        )
        self._text_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator(foreground="green")]
        )
        self._legal_renderer: TextRenderer = create_text_renderer(
            decorators=[
                ColorDecorator(foreground="lightyellow"),
                WriteOnceDecorator(state_filename="legal"),
            ]
        )
        self._notice_renderer: TextRenderer = create_text_renderer(
            decorators=[ColorDecorator(foreground="lightyellow")]
        )
        self._error_renderer: TextRenderer = create_error_renderer()
        self._warning_renderer: TextRenderer = create_warning_renderer()

        # Proxy objects
        self._proxy = CHAT_IDENTIFIER.get_proxy()
        self._user_proxy = USER_IDENTIFIER.get_proxy()
        self._history_proxy = HISTORY_IDENTIFIER.get_proxy()

        super().__init__()

    def _get_input_source(self) -> str:
        """Determine and return the appropriate input source based on combination rules.

        Warning:
            This is set to be deprecated in the future when we normalize the API backend to accept the context and works with it.

        Rules:
        1. Positional query only -> use positional query
        2. Stdin query only -> use stdin query
        3. File query only -> use file query
        4. Stdin + positional query -> combine as "{positional_query} {stdin}"
        5. Stdin + file query -> combine as "{stdin} {file_query}"
        6. Positional + file query -> combine as "{positional_query} {file_query}"
        7. All three sources -> use only positional and file as "{positional_query} {file_query}"

        Raises:
            ValueError: If no input source is provided

        Returns:
            str: The query string from the selected input source(s)
        """
        # Rule 7: All three present - positional and file take precedence
        if all([self._query, self._stdin, self._attachment]):
            self._warning_renderer.render(
                "Using positional query and file input. Stdin will be ignored."
            )
            return f"{self._query} {self._attachment}"

        # Rule 6: Positional + file
        if self._query and self._attachment:
            return f"{self._query} {self._attachment}"

        # Rule 5: Stdin + file
        if self._stdin and self._attachment:
            return f"{self._stdin} {self._attachment}"

        # Rule 4: Stdin + positional
        if self._stdin and self._query:
            return f"{self._query} {self._stdin}"

        # Rules 1-3: Single source - return first non-empty source
        source = next(
            (src for src in [self._query, self._stdin, self._attachment] if src),
            None,
        )
        if source:
            return source

        raise ValueError(
            "No input provided. Please provide input via file, stdin, or direct query."
        )

    def _chat_management(self, user_id: str, args: Namespace) -> int:
        """Manage the chat sessions based on the arguments provided.

        Args:
            user_id (str): The user identifier
            args (Namespace): The arguments processed with argparse.

        Returns:
            int: Status code of the execution
        """
        if args.list:
            all_chats = ChatList.from_structure(self._proxy.GetAllChatFromUser(user_id))

            if not all_chats.chats:
                self._text_renderer.render("No chats available.")
                return 0

            self._text_renderer.render(
                f"Found a total of {len(all_chats.chats)} chats:"
            )
            for index, chat in enumerate(all_chats.chats):
                self._text_renderer.render(
                    f"{index}. Chat: {chat.name} - {chat.description} (created at: {chat.created_at})"
                )

        if args.delete:
            try:
                self._proxy.DeleteChatForUser(user_id, args.delete)
                self._text_renderer.render(f"Chat {args.delete} deleted successfully.")
            except ChatNotFoundError as e:
                self._error_renderer.render(str(e))
                return 1

        if args.delete_all:
            try:
                self._proxy.DeleteAllChatForUser(user_id)
                self._text_renderer.render("Deleted all chats successfully.")
            except ChatNotFoundError as e:
                self._error_renderer.render(str(e))
                return 1

        return 0

    def _chat_question(self, user_id: str, args: Namespace) -> int:
        """Manage chat question

        Arguments:
            user_id (str): The user identifier
            args (Namespace): The arguments processed with argparse.

        Returns:
            int: Status code of the execution
        """
        try:
            question = self._get_input_source()
        except ValueError as e:
            self._error_renderer.render(str(e))
            return 1

        response = "Nothing to see here..."

        try:
            with self._spinner_renderer:
                chat_id = self._create_chat_session(user_id)
                response = self._get_response(user_id, chat_id, question)
                self._history_proxy.WriteHistory(chat_id, user_id, question, response)
        except (
            RequestFailedError,
            MissingHistoryFileError,
            CorruptedHistoryError,
        ) as e:
            self._error_renderer.render(str(e))
            return 1

        self._legal_renderer.render(LEGAL_NOTICE)
        self._text_renderer.render(response)
        self._notice_renderer.render(ALWAYS_LEGAL_MESSAGE)
        return 0

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Status code of the execution
        """
        user_id = self._get_user_id()
        if self._args.list or self._args.delete or self._args.delete_all:
            return self._chat_management(user_id, self._args)

        return self._chat_question(user_id, self._args)

    def _get_user_id(self) -> str:
        """Get the user ID based on the effective user ID.

        Returns:
            str: The user ID
        """
        return self._user_proxy.GetUserId(self._context.effective_user_id)

    def _get_response(self, user_id: str, chat_id: str, question: str) -> str:
        """Get the response from the chat session.

        Arguments:
            user_id (str): The user identifier
            chat_id (str): The chat session identifier
            question (str): The question to be asked

        Returns:
            str: The response from the chat session
        """
        message_input = Question(
            message=question,
            stdin=StdinInput(stdin=self._stdin),
            attachment=AttachmentInput(
                contents=self._attachment, mimetype=self._attachment_mimetype
            ),
        )
        response = self._proxy.AskQuestion(
            user_id,
            message_input.structure(),
        )

        return Response.from_structure(response).message

    def _create_chat_session(self, user_id: str) -> str:
        """Create a new chat session for a given conversation.

        Arguments:
            user_id (str): The user identifier

        Returns:
            str: The identifier of the chat session.
        """
        has_chat_id = None
        try:
            has_chat_id = self._proxy.GetChatId(user_id, self._args.name)
        except ChatNotFoundError:
            # It's okay to swallow this exception as if there is no chat for
            # this user, we will create one.
            pass

        # To avoid doing this check inside the CreateChat method, let's do it
        # in here.
        if has_chat_id:
            return has_chat_id

        return self._proxy.CreateChat(
            user_id,
            self._args.name,
            self._args.description,
        )


def register_subcommand(parser: SubParsersAction) -> None:
    """
    Register this command to argparse so it's available for the root parserself._.

    Args:
        parser (SubParsersAction): Root parser to register command-specific arguments
    """
    chat_parser = parser.add_parser(
        "chat",
        help="Command to ask a question to the LLM.",
    )

    question_group = chat_parser.add_argument_group("Question options")
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

    chat_arguments = chat_parser.add_argument_group("Chat options")
    chat_arguments.add_argument(
        "-l", "--list", action="store_true", help="List all chats"
    )
    chat_arguments.add_argument(
        "-d", "--delete", nargs="?", help="Delete a chat session", default=""
    )
    chat_arguments.add_argument(
        "-da", "--delete-all", action="store_true", help="Delete all chats"
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

    Args:
        args (Namespace): The arguments processed with argparse.

    Returns:
        QueryCommand: Return an instance of class
    """
    return ChatCommand(args)
