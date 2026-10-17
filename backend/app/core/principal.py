"""
Auth Principal Model — pure Pydantic model representing an authenticated actor (User or API Key/System).
Decoupled from UserEntity domain entity.
"""

from enum import Enum
from fastapi import status
from pydantic import BaseModel, ConfigDict, Field

from app.shared.application.response import BadRequestException


class PrincipalType(str, Enum):
    USER = "USER"
    API_KEY = "API_KEY"


class AuthPrincipal(BaseModel):
    """
    Represents an authenticated principal (actor) in the request context.
    Can be a human user (authenticated via JWT) or a system/service (authenticated via API Key).
    """

    model_config = ConfigDict(frozen=False)

    actor_id: int | None = None
    actor_type: PrincipalType
    name: str
    email: str | None = None
    role_names: list[str] = Field(default_factory=list)
    permissions: set[str] = Field(default_factory=set)

    def has_permission(self, permission_name: str) -> bool:
        """
        Check if the principal has a specific permission.
        Admin role automatically grants all permissions.
        """
        if any(r.lower() == "admin" for r in self.role_names):
            return True
        return permission_name in self.permissions

    @property
    def is_user(self) -> bool:
        """Check if the principal is a human user."""
        return self.actor_type == PrincipalType.USER

    @property
    def is_api_key(self) -> bool:
        """Check if the principal is a system/service account via API Key."""
        return self.actor_type == PrincipalType.API_KEY

    @property
    def id(self) -> int | None:
        """
        Backwards-compatible user ID accessor.
        Returns user ID if principal is a human user, otherwise None for API Key.
        """
        return self.actor_id if self.is_user else None

    @property
    def user_id(self) -> int:
        """
        Get user ID safely.
        Raises 403 Forbidden if accessed by a machine/API Key principal.
        """
        if not self.is_user or self.actor_id is None:
            raise BadRequestException(
                message="Thao tác chỉ dành cho tài khoản người dùng cá nhân",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return self.actor_id
