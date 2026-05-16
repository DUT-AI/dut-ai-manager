"""
User Domain Entity — pure Pydantic, NO ORM dependency.
"""

from enum import Enum

from pydantic import Field

from app.shared.domain.base_entity import BaseEntity


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class UserEntity(BaseEntity):
    """Domain entity representing a user."""

    name: str
    email: str
    phone_number: str | None = None
    status: UserStatus = UserStatus.ACTIVE
    avatar_url: str | None = None

    # IDs for external services
    discord_id: str | None = None
    check_in_card_code: str | None = None
    zalo_id: str | None = None
    zalo_bot_id: str | None = None
    zalo_bind_code: str | None = None

    # Relationship IDs
    role_id: int | None = None

    # Denormalized / Virtual fields (populated by repository)
    role_name: str | None = None
    permissions: set[str] = Field(default_factory=set)

    def has_permission(self, permission_name: str) -> bool:
        if self.role_name == "admin":
            return True
        return permission_name in self.permissions

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE
