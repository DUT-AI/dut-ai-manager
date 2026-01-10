from typing import TYPE_CHECKING, List, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.models.role_permission import RolePermission


class Permission(TimestampMixin, table=True):
    """Permission model for RBAC"""

    __tablename__ = "permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(
        max_length=100, unique=True, index=True
    )  # e.g., "user:read", "user:write"
    description: Optional[str] = Field(default=None, max_length=255)
    resource: str = Field(
        max_length=100, index=True
    )  # e.g., "user", "role", "permission"
    action: str = Field(max_length=50)  # e.g., "create", "read", "update", "delete"

    # Relationships - use string for forward reference
    role_permissions: List["RolePermission"] = Relationship(back_populates="permission")
