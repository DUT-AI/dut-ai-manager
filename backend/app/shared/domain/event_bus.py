"""
Simple in-process Domain Event Bus.

Enables decoupled cross-module communication:
    - Use Cases publish events after business operations
    - Handlers (e.g. NotificationHandler) subscribe and react

Usage:
    # Define event
    class ViolationCreated(DomainEvent):
        violation_id: int
        user_id: int

    # Subscribe handler
    EventBus.subscribe(ViolationCreated, handle_violation_created)

    # Publish in Use Case
    await EventBus.publish(ViolationCreated(violation_id=1, user_id=42))
"""

from typing import Any, Callable, Coroutine

from pydantic import BaseModel


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    pass


class EventBus:
    """Simple in-process event bus for domain events."""

    _handlers: dict[type, list[Callable[..., Coroutine[Any, Any, None]]]] = {}

    @classmethod
    def subscribe(
        cls,
        event_type: type[DomainEvent],
        handler: Callable[..., Coroutine[Any, Any, None]],
    ) -> None:
        """Register an async handler for an event type."""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)

    @classmethod
    async def publish(cls, event: DomainEvent) -> None:
        """Publish an event to all registered handlers."""
        handlers = cls._handlers.get(type(event), [])
        for handler in handlers:
            await handler(event)

    @classmethod
    def clear(cls) -> None:
        """Clear all handlers (useful for testing)."""
        cls._handlers.clear()
