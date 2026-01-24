from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.permission import Permission
    from app.models.role_permission import RolePermission


class RoleType(str, Enum):
    """Role type enum"""

    ADMIN = "admin"  # Chủ nhiệm
    LEADER = "leader"  # Trưởng nhóm
    TEAMMATE = "teammate"  # Thành viên


class Role(TimestampMixin, table=True):
    """Role model for RBAC"""

    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=255)

    # Relationships - use string for forward reference
    users: List["User"] = Relationship(
        back_populates="role", sa_relationship_kwargs={"foreign_keys": "[User.role_id]"}
    )
    role_permissions: List["RolePermission"] = Relationship(back_populates="role")

    @property
    def permissions(self) -> List["Permission"]:
        return [rp.permission for rp in self.role_permissions if rp.permission]
