"""Email service interface for domain layer."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class IEmailService(Protocol):
    """Interface for sending emails. Implementation lives in infrastructure."""

    async def send_welcome_email(self, to_email: str, name: str, password: str) -> None:
        """Send welcome email with account credentials to a new user."""
        ...
