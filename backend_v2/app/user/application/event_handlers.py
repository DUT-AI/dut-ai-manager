"""Event handlers for User module side-effects."""

from app.shared.email_service import IEmailService
from app.user.domain.events import UserCreatedEvent
from loguru import logger


class SendWelcomeEmailHandler:
    """Handles UserCreatedEvent by sending a welcome email."""

    def __init__(self, email_service: IEmailService) -> None:
        self._email_service = email_service

    async def handle(self, event: UserCreatedEvent) -> None:
        logger.info(f"Sending welcome email to {event.email}")
        await self._email_service.send_welcome_email(
            to_email=event.email,
            name=event.name,
            password=event.plain_password,
        )
