"""Simplified history command implementation."""

import logging
from argparse import Namespace

from command_line_assistant.commands.cli import (
    CommandContext,
    argument,
    command,
)
from command_line_assistant.dbus.client import DbusClient
from command_line_assistant.dbus.exceptions import (
    HistoryNotAvailableError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.structures.chat import ChatList
from command_line_assistant.dbus.structures.history import HistoryList
from command_line_assistant.exceptions import HistoryCommandException
from command_line_assistant.rendering.colors import colorize
from command_line_assistant.rendering.renderers import (
    Renderer,
    format_datetime,
)
from command_line_assistant.rendering.theme import Theme

logger = logging.getLogger(__name__)


def _show_history(renderer: Renderer, entries: HistoryList) -> None:
    """Display history entries in a standardized way.

    Args:
        renderer (Renderer): The renderer.
        entries (HistoryList): The list of history entries.
    """

    if not entries.histories:
        renderer.normal("No history entries found")
        return

    for entry in entries.histories:
        # Render question block
        question_text = f"## 🤔 Question\n{entry.question}\n"
        renderer.markdown(question_text)

        # Add a small spacing
        renderer.normal("")

        # Render answer block
        answer_text = f"## 🤖 Answer\n{entry.response}\n"
        renderer.markdown(answer_text)

        from_chat_message = f"\n*From chat: {entry.chat_name}*\n"
        renderer.markdown(colorize(from_chat_message, "yellow"))

        created_at_message = f"*Created at: {format_datetime(entry.created_at)}*\n"
        renderer.markdown(colorize(created_at_message, "yellow"))

        # Add separator between entries if needed
        if len(entries.histories) > 1:
            renderer.normal("\n" + "═" * (len(created_at_message) - 1) + "\n")


@command("history", help="Manage Conversation History")
@argument(
    "--from-chat",
    help="Specify from which chat we should retrieve the history. Default chat is 'default'",
    default="default",
)
@argument(
    "-f",
    "--first",
    action="store_true",
    help="Get the first conversation from history.",
)
@argument(
    "-l", "--last", action="store_true", help="Get the last conversation from history."
)
@argument("--filter", help="Search for a specific keyword of text in the history.")
@argument("-a", "--all", action="store_true", help="Get all the conversation history.")
@argument(
    "-c",
    "--clear",
    action="store_true",
    help="Clear the entire history for a given chat. Use --from-chat with its given name to clear that particular history.",
)
@argument("--clear-all", action="store_true", help="Clear the entire history.")
def history_command(args: Namespace, context: CommandContext) -> int:
    """History command implementation.

    Args:
        args (Namespace): Command line arguments.
        context (CommandContext): Command context.

    Returns:
        int: Exit code.
    """
    dbus = DbusClient()
    render = Renderer(args.plain, theme=Theme())

    user_id = dbus.user_proxy.GetUserId(context.effective_user_id)

    try:
        is_chat_available = dbus.chat_proxy.IsChatAvailable(user_id, args.from_chat)

        if not is_chat_available:
            raise HistoryCommandException(
                f"Nothing to clean as {args.from_chat} chat is not available. Try asking something first."
            )

        # Determine which operation to perform
        if args.clear:
            return _clear_history(render, dbus, user_id, args.from_chat)
        elif args.clear_all:
            return _clear_all_history(render, dbus, user_id)
        elif args.first:
            return _first_history(render, dbus, user_id, args.from_chat, args.plain)
        elif args.last:
            return _last_history(render, dbus, user_id, args.from_chat, args.plain)
        elif args.filter:
            return _filter_history(
                render, dbus, user_id, args.filter, args.from_chat, args.plain
            )
        else:
            # Default to showing all history
            return _all_history(render, dbus, user_id, args.plain)
    except HistoryCommandException as e:
        logger.info("Failed to execute history command: %s", str(e))
        render.error(str(e))
        return e.code


def _clear_history(
    render: Renderer, dbus: DbusClient, user_id: str, from_chat: str
) -> int:
    """Clear history for a specific chat.

    Args:
        render (RenderUtils): The render utils.
        dbus (DbusUtils): The dbus utils.
        user_id (str): The user id.
        from_chat (str): The chat id.

    Returns:
        int: The exit code.
    """
    try:
        dbus.history_proxy.ClearHistory(user_id, from_chat)
        render.normal("History cleaned successfully.")
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug("Failed to clear the history: %s", str(e))
        raise HistoryCommandException(str(e)) from e


def _clear_all_history(render: Renderer, dbus: DbusClient, user_id: str) -> int:
    """Clear all history.

    Args:
        render (RenderUtils): The render utils.
        dbus (DbusUtils): The dbus utils.
        user_id (str): The user id.

    Returns:
        int: The exit code.
    """
    try:
        all_user_chats = ChatList.from_structure(
            dbus.chat_proxy.GetAllChatFromUser(user_id)
        )

        if not all_user_chats.chats:
            raise HistoryCommandException(
                "Nothing to clean as there is no chat session in place."
            )

        dbus.history_proxy.ClearAllHistory(user_id)
        render.normal("All histories cleared successfully.")
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug(
            "An error occurred while trying to clear all histories: %s", str(e)
        )
        raise HistoryCommandException(str(e)) from e


def _first_history(
    render: Renderer, dbus: DbusClient, user_id: str, from_chat: str, plain: bool
) -> int:
    """Get first conversation from history.

    Args:
        render (RenderUtils): The render utils.
        dbus (DbusUtils): The dbus utils.
        user_id (str): The user id.
        from_chat (str): The chat id.
        plain (bool): Whether to render in plain text.

    Returns:
        int: The exit code.
    """
    try:
        render.normal("Getting first conversation from history.")
        response = dbus.history_proxy.GetFirstConversation(user_id, from_chat)
        history = HistoryList.from_structure(response)
        _show_history(render, history)
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug("Failed to retrieve the first history entry: %s", str(e))
        raise HistoryCommandException(str(e)) from e


def _last_history(
    render: Renderer, dbus: DbusClient, user_id: str, from_chat: str, plain: bool
) -> int:
    """Get last conversation from history.

    Args:
        render (RenderUtils): The render utils.
        dbus (DbusUtils): The dbus utils.
        user_id (str): The user id.
        from_chat (str): The chat id.
        plain (bool): Whether to render in plain text.

    Returns:
        int: The exit code.
    """
    try:
        render.normal("Getting last conversation from history.")
        response = dbus.history_proxy.GetLastConversation(user_id, from_chat)
        history = HistoryList.from_structure(response)
        _show_history(render, history)
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug("Failed to retrieve the last history entry: %s", str(e))
        raise HistoryCommandException(str(e)) from e


def _filter_history(
    render: Renderer,
    dbus: DbusClient,
    user_id: str,
    filter_text: str,
    from_chat: str,
    plain: bool,
) -> int:
    """Filter conversation history.

    Args:
        render (RenderUtils): The render utils.
        dbus (DbusUtils): The dbus utils.
        user_id (str): The user id.
        filter_text (str): The filter text.
        from_chat (str): The chat id.
        plain (bool): Whether to render in plain text.

    Returns:
        int: The exit code.
    """
    try:
        render.normal("Filtering conversation history.")
        response = dbus.history_proxy.GetFilteredConversation(
            user_id, filter_text, from_chat
        )
        history = HistoryList.from_structure(response)
        _show_history(render, history)
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug(
            "Failed to retrieve entries with filter '%s': %s",
            filter_text,
            str(e),
        )
        raise HistoryCommandException(str(e)) from e


def _all_history(render: Renderer, dbus: DbusClient, user_id: str, plain: bool) -> int:
    """Get all conversation history.

    Args:
        render (RenderUtils): The render utils.
        dbus (DbusUtils): The dbus utils.
        user_id (str): The user id.
        plain (bool): Whether to render in plain text.

    Returns:
        int: The exit code.
    """
    try:
        render.normal("Getting all conversations from history.")
        response = dbus.history_proxy.GetHistory(user_id)
        history = HistoryList.from_structure(response)
        _show_history(render, history)
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug("Failed to retrieve the all history entries: %s", str(e))
        raise HistoryCommandException(str(e)) from e
