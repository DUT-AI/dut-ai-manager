"""Domain events emitted by the User module."""

from dataclasses import dataclass

from app.shared.event_bus import DomainEvent


@dataclass
class UserCreatedEvent(DomainEvent):
    """Emitted when a new user is created with an account."""

    user_id: int = 0
    email: str = ""
    name: str = ""
    plain_password: str = ""
