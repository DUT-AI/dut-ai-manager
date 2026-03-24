from datetime import datetime
from typing import Optional

from app.shared.base_entity import BaseEntity
from app.user.domain.value_objects import UserStatus
from pydantic import EmailStr


class User(BaseEntity):
    """Domain entity representing a user."""

    name: str = ""
    email: EmailStr
    phone_number: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    discord_id: Optional[str] = None
    zalo_id: Optional[str] = None
    zalo_bot_id: Optional[str] = None
    zalo_bind_code: Optional[str] = None
    avatar_url: Optional[str] = None
    role_id: Optional[int] = None
    account_id: Optional[int] = None

    def deactivate(self) -> None:
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def update_settings(
        self, avatar_url: Optional[str] = None, discord_id: Optional[str] = None
    ) -> None:
        if avatar_url is not None:
            self.avatar_url = avatar_url
        if discord_id is not None:
            self.discord_id = discord_id
        self.updated_at = datetime.utcnow()
