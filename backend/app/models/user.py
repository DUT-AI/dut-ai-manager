from enum import Enum
from typing import TYPE_CHECKING, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.role import Role
    from app.models.permission_request import PermissionRequest
    from app.models.activity import BonusPoint, Violation
    from app.models.team import TeamMember


class UserStatus(str, Enum):
    """User status enum"""

    ACTIVE = "active"
    INACTIVE = "inactive"


class User(TimestampMixin, table=True):
    """User model"""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    email: str = Field(max_length=255, unique=True, index=True)
    status: UserStatus = Field(default=UserStatus.ACTIVE)

    # Foreign keys
    role_id: Optional[int] = Field(default=None, foreign_key="roles.id", index=True)
    account_id: Optional[int] = Field(
        default=None, foreign_key="accounts.id", unique=True
    )

    # Relationships - use string for forward reference
    role: Optional["Role"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"foreign_keys": "[User.role_id]"},
    )
    account: Optional["Account"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[User.account_id]"},
    )
    bonus_points: list["BonusPoint"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[BonusPoint.user_id]"},
    )
    violations: list["Violation"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Violation.user_id]"},
    )
    team_members: list["TeamMember"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[TeamMember.user_id]"},
    )

    @property
    def role_name(self) -> Optional[str]:
        if self.role:
            return self.role.name.value
        return None

    @property
    def permissions(self) -> set[str]:
        if not self.role:
            return set()
        return {
            rp.permission.name for rp in self.role.role_permissions if rp.permission
        }

    def has_permission(self, permission_name: str) -> bool:
        if self.role and self.role.name.value == "admin":
            return True
        return permission_name in self.permissions
