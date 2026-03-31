"""Shared event bus interfaces and base classes for Domain Events."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, TypeVar, runtime_checkable
from uuid import uuid4


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


T_Event = TypeVar("T_Event", bound=DomainEvent, contravariant=True)


@runtime_checkable
class IEventHandler(Protocol[T_Event]):
    """Interface for event handlers. Generic over the event type."""

    async def handle(self, event: T_Event) -> None: ...


@runtime_checkable
class IEventBus(Protocol):
    """Interface for publishing domain events."""

    def subscribe(self, event_type: type[DomainEvent], handler: "IEventHandler[DomainEvent]") -> None:
        """Register a handler for an event type."""
        ...

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers."""
        ...

