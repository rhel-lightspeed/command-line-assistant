"""Module that holds the exceptions for the client part of the codebase."""


class StopInteractiveMode(Exception):
    """Control the interactive mode execution"""


class ChatCommandException(Exception):
    """Exception class to control chat command."""

    code: int = 80


class ShellCommandException(Exception):
    """Exception class to control shell command."""

    code: int = 81


class HistoryCommandException(Exception):
    """Exception class to control history command."""

    code: int = 82


class FeedbackCommandException(Exception):
    """Exception class to control feedback command."""

    code: int = 83
