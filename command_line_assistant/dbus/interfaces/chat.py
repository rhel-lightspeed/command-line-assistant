"""D-Bus interfaces that defines and powers our commands."""

import logging

from dasbus.server.interface import dbus_interface
from dasbus.server.template import InterfaceTemplate
from dasbus.typing import Str, Structure

from command_line_assistant.daemon.database.manager import DatabaseManager
from command_line_assistant.daemon.database.repository.chat import ChatRepository
from command_line_assistant.daemon.http.query import submit
from command_line_assistant.dbus.constants import CHAT_IDENTIFIER
from command_line_assistant.dbus.context import DaemonContext
from command_line_assistant.dbus.exceptions import ChatNotFoundError
from command_line_assistant.dbus.structures.chat import (
    ChatEntry,
    ChatList,
    Question,
    Response,
)

audit_logger = logging.getLogger("audit")
logger = logging.getLogger(__name__)


@dbus_interface(CHAT_IDENTIFIER.interface_name)
class ChatInterface(InterfaceTemplate):
    """The DBus interface of a query."""

    def __init__(self, implementation: DaemonContext):
        """Constructor of the class

        Arguments:
            implementation (DaemonContext): The implementation context to be used in an interface.
        """
        super().__init__(implementation)

        self._db_manager = DatabaseManager(implementation.config)
        self._chat_repository = ChatRepository(self._db_manager)

    def GetAllChatFromUser(self, user_id: Str) -> Structure:
        """Get all the chat session for a given user.

        Arguments:
            user_id (Str): The identifier of the user.

        Returns:
            Structure: The list of chat sessions.
        """
        result = self._chat_repository.select_all_by_id(user_id)

        chat_entries = []
        for entry in result:
            chat_entries.append(
                ChatEntry(
                    str(entry.id),
                    entry.name,
                    entry.description,
                    str(entry.created_at),
                    str(entry.updated_at),
                    str(entry.deleted_at),
                )
            )

        return ChatList(chat_entries).structure()

    def DeleteAllChatForUser(self, user_id: Str) -> None:
        """Delete all chats from the user.

        Arguments:
            user_id (Str): The identifier of the user.

        Raises:
            ChatNotFoundError: In case no chat was found for the current user.
        """
        all_chats = self._chat_repository.select_all_by_id(user_id)

        if not all_chats:
            raise ChatNotFoundError("No chat found to delete.")

        for chat in all_chats:
            logger.info("Deleting chat '%s' for user '%s", chat.id, user_id)
            self._chat_repository.delete(chat.id)

    def DeleteChatForUser(self, user_id: Str, name: Str) -> None:
        """Delete a specific chat for a user.

        Arguments:
            user_id (Str): The identifier of the user.
            name (Str): The name of the chat.

        Raises:
            ChatNotFoundError: In case no chat was found with the given name for the current user.
        """
        logger.info("Looking for chat '%s' on user '%s'", name, user_id)
        chat = self._chat_repository.select_by_name(user_id, name)

        if not chat:
            logger.info(
                "Couldn't find chat with name '%s' for user '%s'. Either the name is not correct or the chat does not exist.",
                name,
                user_id,
            )
            raise ChatNotFoundError(
                f"Couldn't find chat with name '{name}'. Check the name requested and try again."
            )

        logger.info(
            "Found chat '%s' for user '%s'. Deleteing it as requested.",
            chat.id,
            user_id,
        )
        self._chat_repository.delete(chat.id)

    def GetLatestChatFromUser(self, user_id: Str) -> Str:
        """Get the latest chat session for a given user.

        Arguments:
            user_id (Str): The identifier of the user.

        Returns:
            Str: The identifier of the chat session.
        """
        result = self._chat_repository.select_latest_chat(user_id)
        return str(result.id)

    def GetChatId(self, user_id: Str, name: Str) -> Str:
        """Get the chat id for a given user and chat name.

        Arguments:
            user_id (Str): The identifier of the user.
            name (Str): The name of the chat.

        Raises:
            ChatNotFound: If the chat is not found.

        Returns:
            Str: The identifier of the chat session.
        """
        result = self._chat_repository.select_by_name(user_id, name)

        if not result:
            raise ChatNotFoundError(
                f"No chat found with name '{name}'. Please, make sure that this chat exist first."
            )

        logger.info(
            "Found existing chat with id '%s' and name '%s' for user '%s'",
            result.id,
            name,
            user_id,
        )
        return str(result.id)

    def CreateChat(self, user_id: Str, name: Str, description: Str) -> Str:
        """Create a new chat session for a given conversation.

        Arguments:
            user_id (Str): The identifier of the user.
            name (Str): The name of the chat. If not specified, a random name will be given.
            description (Str): A description for the chat to identify the context of it.

        Returns:
            Str: The identifier of the chat session.
        """
        result = self._chat_repository.select_by_name(user_id, name)
        if result:
            logger.info(
                "Found existing chat with id '%s' and name '%s' for user '%s'",
                result.id,
                name,
                user_id,
            )
            logger.info("Skipping the creation of a new chat entry.")
            return str(result.id)

        identifier = self._chat_repository.insert(
            {"user_id": user_id, "name": name, "description": description}
        )
        logger.info(
            "New chat session created with id '%s' and name '%s'", identifier, name
        )
        return str(identifier)

    def AskQuestion(
        self, chat_id: Str, user_id: Str, message_input: Structure
    ) -> Structure:
        """This method is mainly called by the client to retrieve it's answer.

        Arguments:
            chat_id (Str): The identifier of the chat session.
            user_id (Str): The identifier of the user.
            message_input (Structure): The message input in format of a d-bus structure.

        Returns:
            Structure: The message output in format of a d-bus structure.
        """
        content = Question.from_structure(message_input)
        # Submit query to backend
        data = {
            "question": content.message,
            "context": {
                "stdin": content.stdin.stdin,
                "attachments": {
                    "contents": content.attachment.contents,
                    "mimetype": content.attachment.mimetype,
                },
            },
        }
        llm_response = submit(data, self.implementation.config)

        # Create message object
        response = Response(llm_response)

        audit_logger.info(
            "Query executed successfully.",
            extra={
                "user": user_id,
                "query": content.message,
                "response": llm_response,
            },
        )
        # Return the data
        return response.structure()
