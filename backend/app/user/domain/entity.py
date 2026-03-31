"""
User Domain Entity — pure Pydantic, NO ORM dependency.
"""

from enum import Enum
from typing import Optional
from pydantic import Field

from app.shared.domain.base_entity import BaseEntity


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class User(BaseEntity):
    """Domain entity representing a user."""

    name: str
    email: str
    phone_number: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    avatar_url: Optional[str] = None
    
    # IDs for external services
    discord_id: Optional[str] = None
    zalo_id: Optional[str] = None
    zalo_bot_id: Optional[str] = None
    zalo_bind_code: Optional[str] = None

    # Relationship IDs
    role_id: Optional[int] = None
    account_id: Optional[int] = None

    # Denormalized / Virtual fields (populated by repository)
    role_name: Optional[str] = None
    permissions: set[str] = Field(default_factory=set)

    def has_permission(self, permission_name: str) -> bool:
        if self.role_name == "admin":
            return True
        return permission_name in self.permissions
