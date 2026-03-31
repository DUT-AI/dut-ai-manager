from typing import Optional, Protocol

from app.auth.application.dtos import UserAuthContextDTO
from app.auth.domain.auth_user_entity import AuthUser


class IAuthUserRepository(Protocol):
    async def get_by_email(self, email: str) -> Optional[AuthUser]: ...

    async def get_by_id(self, user_id: int) -> Optional[AuthUser]: ...

    async def update_password(self, user_id: int, new_hashed_password: str) -> None: ...


class IPasswordHasher(Protocol):
    def hash(self, raw_password: str) -> str: ...

    def verify(self, raw_password: str, hashed_password: str) -> bool: ...


class ITokenService(Protocol):
    def create_access_token(self, payload: dict) -> str: ...

    def create_refresh_token(self, payload: dict) -> str: ...

    def decode_token(self, token: str) -> dict: ...


class IAuthQueryService(Protocol):
    async def get_user_auth_context_by_email(
        self, email: str
    ) -> Optional["UserAuthContextDTO"]: ...


class IAccountCreator(Protocol):
    """Interface for creating authentication accounts.
    Auth module exposes this for other modules (e.g. User) to use.
    """

    async def create_account(self) -> tuple[int, str]:
        """Create a new account with a generated password.
        Returns: (account_id, plain_password)
        """
        ...
