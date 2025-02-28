"""Module that holds the exceptions for the client part of the codebase."""


class StopInteractiveMode(Exception):
    """Control the interactive mode execution"""


class ChatCommandException(Exception):
    """Exception class to control chat command."""


class ShellCommandException(Exception):
    """Exception class to control shell command."""


class HistoryCommandException(Exception):
    """Exception class to control history command."""


class FeedbackCommandException(Exception):
    """Exception class to control feedback command."""
