"""Request-scoped context using contextvars.

Provides the current user ID to any layer (especially SQLAlchemy events)
without passing it explicitly through every function call.
"""

from contextvars import ContextVar

# Holds the authenticated user's ID for the current request.
# None when unauthenticated or during system operations (seed, cron, etc.).
current_user_id_var: ContextVar[int | None] = ContextVar("current_user_id", default=None)
