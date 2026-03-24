"""AccountCreator service — creates auth accounts with generated passwords."""

import secrets
import string

from app.auth.domain.interfaces import IPasswordHasher
from app.auth.infrastructure.account_model import AccountModel
from sqlalchemy.ext.asyncio import AsyncSession


class AccountCreatorService:
    """Creates a new account record with a strong random password."""

    def __init__(self, session: AsyncSession, hasher: IPasswordHasher) -> None:
        self._session = session
        self._hasher = hasher

    async def create_account(self) -> tuple[int, str]:
        """Create account and return (account_id, plain_password)."""
        password = self._generate_strong_password()
        hashed = self._hasher.hash(password)

        account = AccountModel(hash_password=hashed)
        self._session.add(account)
        await self._session.flush()  # Get the generated ID without committing

        return account.id, password  # type: ignore[return-value]

    @staticmethod
    def _generate_strong_password(length: int = 12) -> str:
        """Generate a strong random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = "".join(secrets.choice(alphabet) for _ in range(length))
            # Ensure at least one of each required character type
            if (
                any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%^&*" for c in password)
            ):
                return password
