"""Shared event bus interfaces and base classes for Domain Events."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@runtime_checkable
class IEventHandler(Protocol):
    """Interface for event handlers."""

    async def handle(self, event: DomainEvent) -> None: ...


@runtime_checkable
class IEventBus(Protocol):
    """Interface for publishing domain events."""

    def subscribe(self, event_type: type[DomainEvent], handler: IEventHandler) -> None:
        """Register a handler for an event type."""
        ...

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers."""
        ...
