from abc import ABC, abstractmethod
from typing import List, Optional

from app.user.domain.user_entity import User, UserStatus


class IUserRepository(ABC):
    """Abstract repository interface in domain layer."""

    @abstractmethod
    async def get_by(
        self, user_id: int | None = None, email: str | None = None
    ) -> Optional[User]:
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        pass

    @abstractmethod
    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        role: str | None = None,
        status: UserStatus | None = None,
    ) -> List[User]:
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        pass
