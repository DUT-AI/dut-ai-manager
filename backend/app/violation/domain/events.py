"""
Violation Domain Events.

Events published by violation use cases.
Handlers (e.g. notification) subscribe to react without coupling.
"""

from app.shared.domain.event_bus import DomainEvent


class ViolationCreated(DomainEvent):
    """Published when a violation is created."""

    violation_id: int
    user_id: int
    reason: str
    date: str  # ISO format string for serialization
    user_discord_id: str | None = None
    user_name: str | None = None
    creator_name: str | None = None


class ViolationDeleted(DomainEvent):
    """Published when a violation is soft-deleted."""

    violation_id: int
    user_id: int
