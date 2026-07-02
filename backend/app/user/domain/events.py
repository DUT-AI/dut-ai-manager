from app.shared.domain.event_bus import DomainEvent


class UserCreated(DomainEvent):
    user_id: int
    name: str
    email: str
    role_ids: list[int] = []
