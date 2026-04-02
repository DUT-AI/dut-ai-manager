from app.shared.domain.event_bus import DomainEvent

class AccountCreated(DomainEvent):
    user_id: int
    email: str
    name: str
    password: str
