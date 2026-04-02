from app.auth.domain.service import AuthService
from app.auth.infrastructure.repository import AccountRepository
from app.user.domain.events import UserCreated
from app.auth.domain.events import AccountCreated
from app.shared.domain.event_bus import EventBus
from loguru import logger


class UserAccountHandler:
    """Handles User events to manage Accounts."""

    def __init__(self, auth_service: AuthService, account_repo: AccountRepository):
        self.auth_service = auth_service
        self.account_repo = account_repo

    async def handle(self, event: UserCreated) -> None:
        """Create an account when a new user is created."""
        logger.info(f"Creating account for user_id={event.user_id}")

        password, account = self.auth_service.create_account(user_id=event.user_id)
        self.account_repo.add(account)

        # Publish AccountCreated event (so notification module can send email)
        await EventBus.publish(
            AccountCreated(
                user_id=event.user_id,
                email=event.email,
                name=event.name,
                password=password,
            )
        )

        logger.debug(f"Account created and event published for user {event.email}")
