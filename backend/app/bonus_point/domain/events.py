"""
Bonus Point Domain Events.

Events published by bonus point use cases.
Handlers subscribe to react without coupling.
"""

from app.shared.domain.event_bus import DomainEvent


class BonusPointCreated(DomainEvent):
    """Published when bonus point(s) are created."""

    bonus_point_id: int
    user_id: int
    points: int
    reason: str
    date: str  # ISO format string for serialization
    user_name: str | None = None
    creator_name: str | None = None


class BonusPointUpdated(DomainEvent):
    """Published when a bonus point item is updated."""

    bonus_point_id: int
    user_id: int
    points: int
    reason: str
    date: str
    user_name: str | None = None
    updater_name: str | None = None


class BonusPointDeleted(DomainEvent):
    """Published when a bonus point item is deleted."""

    bonus_point_id: int
    user_id: int
