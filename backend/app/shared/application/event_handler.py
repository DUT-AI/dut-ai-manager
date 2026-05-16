from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.shared.domain.event_bus import DomainEvent

T = TypeVar("T", bound=DomainEvent)


class EventHandler(ABC, Generic[T]):
    """Interface cho tất cả các Domain Event Handlers."""

    @abstractmethod
    async def handle(self, event: T) -> None:
        """Xử lý sự kiện."""
        pass
