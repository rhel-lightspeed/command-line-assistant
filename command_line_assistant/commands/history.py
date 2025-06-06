"""Simplified history command implementation."""

import logging
from argparse import Namespace

from command_line_assistant.dbus.exceptions import (
    HistoryNotAvailableError,
    HistoryNotEnabledError,
)
from command_line_assistant.dbus.structures.chat import ChatList
from command_line_assistant.dbus.structures.history import HistoryList
from command_line_assistant.exceptions import HistoryCommandException
from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.utils.cli import (
    CommandContext,
    argument,
    command,
)
from command_line_assistant.utils.dbus import DbusUtils
from command_line_assistant.utils.renderers import (
    RenderUtils,
    create_markdown_renderer,
    create_text_renderer,
    format_datetime,
)

logger = logging.getLogger(__name__)


def _show_history(entries: HistoryList, plain: bool = False) -> None:
    """Display history entries in a standardized way.

    Args:
        entries (HistoryList): The list of history entries.
        plain (bool, optional): Whether to use plain text rendering. Defaults to False.
    """
    if not entries.histories:
        text_renderer = create_text_renderer(plain=plain)
        text_renderer.render("No history entries found")
        return

    # Create specialized renderers for different parts
    question_renderer = create_markdown_renderer(
        decorators=[ColorDecorator(foreground="cyan")],
        plain=plain,
    )

    answer_renderer = create_markdown_renderer(
        decorators=[ColorDecorator(foreground="green")],
        plain=plain,
    )

    metadata_renderer = create_text_renderer(
        decorators=[ColorDecorator(foreground="yellow")],
        plain=plain,
    )

    text_renderer = create_text_renderer(plain=plain)

    for entry in entries.histories:
        # Render question block
        question_text = f"## 🤔 Question\n{entry.question}"
        question_renderer.render(question_text)

        # Add a small spacing
        text_renderer.render("")

        # Render answer block
        answer_text = f"## 🤖 Answer\n{entry.response}"
        answer_renderer.render(answer_text)

        from_chat_message = f"\n*From chat: {entry.chat_name}*"
        metadata_renderer.render(from_chat_message)

        created_at_message = f"*Created at: {format_datetime(entry.created_at)}*"
        metadata_renderer.render(created_at_message)

        # Add separator between entries if needed
        if len(entries.histories) > 1:
            text_renderer.render("\n" + "═" * (len(created_at_message) - 1) + "\n")


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
    dbus = DbusUtils()
    render = RenderUtils(args.plain)

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
        render.render_error(str(e))
        return e.code


def _clear_history(
    render: RenderUtils, dbus: DbusUtils, user_id: str, from_chat: str
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
        render.render_success("History cleaned successfully.")
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug("Failed to clear the history: %s", str(e))
        raise HistoryCommandException(str(e)) from e


def _clear_all_history(render: RenderUtils, dbus: DbusUtils, user_id: str) -> int:
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
        render.render_success("All histories cleared successfully.")
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug(
            "An error occurred while trying to clear all histories: %s", str(e)
        )
        raise HistoryCommandException(str(e)) from e


def _first_history(
    render: RenderUtils, dbus: DbusUtils, user_id: str, from_chat: str, plain: bool
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
        render.render_success("Getting first conversation from history.")
        response = dbus.history_proxy.GetFirstConversation(user_id, from_chat)
        history = HistoryList.from_structure(response)
        _show_history(history, plain)
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug("Failed to retrieve the first history entry: %s", str(e))
        raise HistoryCommandException(str(e)) from e


def _last_history(
    render: RenderUtils, dbus: DbusUtils, user_id: str, from_chat: str, plain: bool
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
        render.render_success("Getting last conversation from history.")
        response = dbus.history_proxy.GetLastConversation(user_id, from_chat)
        history = HistoryList.from_structure(response)
        _show_history(history, plain)
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug("Failed to retrieve the last history entry: %s", str(e))
        raise HistoryCommandException(str(e)) from e


def _filter_history(
    render: RenderUtils,
    dbus: DbusUtils,
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
        render.render_success("Filtering conversation history.")
        response = dbus.history_proxy.GetFilteredConversation(
            user_id, filter_text, from_chat
        )
        history = HistoryList.from_structure(response)
        _show_history(history, plain)
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug(
            "Failed to retrieve entries with filter '%s': %s",
            filter_text,
            str(e),
        )
        raise HistoryCommandException(str(e)) from e


def _all_history(
    render: RenderUtils, dbus: DbusUtils, user_id: str, plain: bool
) -> int:
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
        render.render_success("Getting all conversations from history.")
        response = dbus.history_proxy.GetHistory(user_id)
        history = HistoryList.from_structure(response)
        _show_history(history, plain)
        return 0
    except (HistoryNotAvailableError, HistoryNotEnabledError) as e:
        logger.debug("Failed to retrieve the all history entries: %s", str(e))
        raise HistoryCommandException(str(e)) from e
