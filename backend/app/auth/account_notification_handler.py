import asyncio

from loguru import logger

from app.auth.domain.events import AccountCreated
from app.shared.infrastructure.email_service import EmailService


class AccountNotificationHandler:
    """Handles Account events to send notifications (Email/Discord)."""

    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: AccountCreated) -> None:
        """Send welcome email when user account is created in background."""

        # We use asyncio.create_task to fire and forget
        # We use asyncio.to_thread because the email_service uses blocking smtplib
        logger.info(f"Scheduling welcome email to {event.email} in background")

        def send_email_sync():
            try:
                self.email_service.send_new_account_email(
                    to_email=event.email, name=event.name, password=event.password
                )
                logger.info(
                    f"Background: Welcome email sent successfully to {event.email}"
                )
            except Exception as e:
                logger.error(
                    f"Background: Failed to send welcome email to {event.email}: {e}"
                )

        # Fire and forget: this doesn't block the handler, and handler returns immediately
        asyncio.create_task(asyncio.to_thread(send_email_sync))
