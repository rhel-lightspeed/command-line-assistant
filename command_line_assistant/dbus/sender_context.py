"""Thread-local storage for sender information."""

import threading
from contextlib import contextmanager

# Thread-local storage for sender information
_sender_context = threading.local()


@contextmanager
def sender_context(sender):
    """Context manager to set sender information in thread-local storage."""
    old_sender = getattr(_sender_context, "sender", None)
    _sender_context.sender = sender
    try:
        yield
    finally:
        if old_sender is not None:
            _sender_context.sender = old_sender
        else:
            delattr(_sender_context, "sender")


def get_current_sender() -> str:
    """Get the current sender from thread-local storage."""
    return getattr(_sender_context, "sender", "")
