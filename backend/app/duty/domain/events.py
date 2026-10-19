"""
Duty Domain Events.
"""

from app.shared.domain.event_bus import DomainEvent


class DutyScheduled(DomainEvent):
    """Event emitted when a duty schedule is created or toggled on."""

    duty_id: int
    team_id: list[int] | int
    team_name: str
    duty_date: str
    meeting_id: int | None = None


class DutySubmitted(DomainEvent):
    """Event emitted when duty evidence is submitted."""

    duty_id: int
    team_id: list[int] | int
    duty_date: str
    submitted_by: int
    image_count: int
    submitted_at: str


class DutyViolated(DomainEvent):
    """Event emitted when duty is not completed by deadline."""

    duty_id: int
    team_id: list[int] | int
    duty_date: str
    penalized_user_ids: list[int]


class DutyUpdated(DomainEvent):
    """Event emitted when a duty's date, time, team or details are updated."""

    duty_id: int
    team_id: list[int] | int
    team_name: str
    duty_date: str
    meeting_id: int | None = None
    is_time_changed: bool = True

