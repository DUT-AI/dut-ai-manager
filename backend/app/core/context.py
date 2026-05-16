"""
Context module for storing request-scoped data using Python's contextvars.
This allows accessing the current user ID from anywhere in the application
without explicitly passing it through function arguments.
"""

from contextvars import ContextVar

# Context variable to store the current user's ID for the request
current_user_id: ContextVar[int | None] = ContextVar("current_user_id", default=None)


def get_current_user_id() -> int | None:
    """Get the current user ID from context."""
    return current_user_id.get()


def set_current_user_id(user_id: int) -> None:
    """Set the current user ID in context."""
    current_user_id.set(user_id)


def clear_current_user_id() -> None:
    """Clear the current user ID from context."""
    current_user_id.set(None)
