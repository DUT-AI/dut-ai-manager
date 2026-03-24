"""In-process event bus implementation using asyncio."""

import asyncio
from collections import defaultdict

from app.shared.event_bus import DomainEvent, IEventHandler
from loguru import logger


class SimpleEventBus:
    """
    Simple in-process event bus.
    Dispatches events to registered handlers asynchronously (fire-and-forget).
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[IEventHandler]] = defaultdict(list)

    def subscribe(
        self, event_type: type[DomainEvent], handler: IEventHandler
    ) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type].append(handler)
        logger.debug(
            f"Subscribed {handler.__class__.__name__} to {event_type.__name__}"
        )

    async def publish(self, event: DomainEvent) -> None:
        """Publish event to all registered handlers (fire-and-forget)."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            logger.warning(f"No handlers registered for {event_type.__name__}")
            return

        for handler in handlers:
            try:
                # Fire-and-forget: create background task
                asyncio.create_task(self._safe_handle(handler, event))
            except Exception as e:
                logger.error(
                    f"Failed to dispatch {event_type.__name__} "
                    f"to {handler.__class__.__name__}: {e}"
                )

    @staticmethod
    async def _safe_handle(handler: IEventHandler, event: DomainEvent) -> None:
        """Safely execute handler, catching and logging any errors."""
        try:
            await handler.handle(event)
            logger.info(
                f"Event {type(event).__name__} handled by "
                f"{handler.__class__.__name__}"
            )
        except Exception as e:
            logger.error(
                f"Error in {handler.__class__.__name__} "
                f"handling {type(event).__name__}: {e}"
            )
