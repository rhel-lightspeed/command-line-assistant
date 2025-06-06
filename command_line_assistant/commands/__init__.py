"""Simplified command registration module."""

# Import all command modules to register them
from command_line_assistant.commands import chat, feedback, history, shell

__all__ = ["chat", "feedback", "history", "shell"]
