"""
Simple in-process Domain Event Bus.

Enables decoupled cross-module communication:
    - Use Cases publish events after business operations
    - Handlers (e.g. NotificationHandler) subscribe and react
"""

from typing import Callable, Union

from pydantic import BaseModel
from loguru import logger
from app.shared.infrastructure.request_context import get_request_container


class DomainEvent(BaseModel):
    """Base class for all domain events."""
        
    pass


class EventBus:
    """Simple in-process event bus for domain events."""

    # Handlers can be either a callable or a class type to be resolved via DI
    _handlers: dict[type, list[Union[Callable, type]]] = {}

    @classmethod
    def subscribe(
        cls,
        event_type: type[DomainEvent],
        handler: Union[Callable, type],
    ) -> None:
        """Register an async handler or a handler type for an event type."""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)

    @classmethod
    async def publish(cls, event: DomainEvent) -> None:
        """Publish an event to all registered handlers."""
        container = get_request_container()
        handler_types = cls._handlers.get(type(event), [])
        
        for handler in handler_types:
            if isinstance(handler, type):
                # If it's a class type, resolve it from Dishka
                if container:
                    try:
                        instance = await container.get(handler)
                        # Convention: Every handler class must have a handle(event) method
                        if hasattr(instance, "handle"):
                            await instance.handle(event)
                        else:
                            logger.error(f"Handler {handler} resolved but has no 'handle' method")
                    except Exception as e:
                        logger.error(f"Error resolving or executing handler {handler}: {e}")
                        raise
                else:
                    logger.warning(f"No container found to resolve handler {handler}")
            else:
                # It's a plain callable
                await handler(event)

    @classmethod
    def clear(cls) -> None:
        """Clear all handlers (useful for testing)."""
        cls._handlers.clear()

    @classmethod
    def print_handlers(cls) -> None:
        """Print all registered handlers."""
        for event_type, handlers in cls._handlers.items():
            logger.info(f"Event: {event_type.__name__}")
            for handler in handlers:
                # Check if it's a type or callable
                name = handler.__name__ if hasattr(handler, "__name__") else str(handler)
                logger.info(f"  Handler: {name}")
