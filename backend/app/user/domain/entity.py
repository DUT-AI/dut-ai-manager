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
    role_ids: list[int] = Field(default_factory=list)

    # Denormalized / Virtual fields (populated by repository)
    role_names: list[str] = Field(default_factory=list)
    permissions: set[str] = Field(default_factory=set)

    def has_permission(self, permission_name: str) -> bool:
        if any(r.lower() == "admin" for r in self.role_names):
            return True
        return permission_name in self.permissions

    @property
    def user_id(self) -> int | None:
        """Alias to match AuthPrincipal.user_id interface."""
        return self.id

    @property
    def is_user(self) -> bool:
        """Matches AuthPrincipal.is_user interface."""
        return True

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE
