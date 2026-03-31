"""
User ORM Model — SQLModel, infrastructure layer.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from app.shared.infrastructure.base_model import TimestampMixin
from sqlmodel import Field, Relationship
from app.user.domain.entity import User as UserEntity, UserStatus

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.role import Role
    from app.violation.infrastructure.model import ViolationModel
    from app.models.team import TeamMember
    from app.models.meeting import MeetingParticipant


class UserModel(TimestampMixin, table=True):
    """ORM model — maps to 'users' table."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    email: str = Field(max_length=255, unique=True, index=True)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    discord_id: Optional[str] = Field(default=None, max_length=255, index=True)
    zalo_id: Optional[str] = Field(default=None, max_length=255, index=True)
    zalo_bot_id: Optional[str] = Field(default=None, max_length=255, index=True)
    zalo_bind_code: Optional[str] = Field(default=None, max_length=10, index=True)
    avatar_url: Optional[str] = Field(default=None)

    # Foreign keys
    role_id: Optional[int] = Field(default=None, foreign_key="roles.id", index=True)
    account_id: Optional[int] = Field(
        default=None, foreign_key="accounts.id", unique=True
    )

    # Relationships
    role: Optional["Role"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"foreign_keys": "[UserModel.role_id]"},
    )
    account: Optional["Account"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[UserModel.account_id]"},
    )
    violations: list["ViolationModel"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[ViolationModel.user_id]"},
    )
    team_members: list["TeamMember"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[TeamMember.user_id]"},
    )
    meeting_participations: list["MeetingParticipant"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[MeetingParticipant.user_id]"},
    )

    def to_entity(self) -> UserEntity:
        """ORM Model → Domain Entity."""
        # Calculate permissions if role is loaded
        permissions = set()
        if self.role and hasattr(self.role, 'role_permissions'):
            permissions = {
                rp.permission.name for rp in self.role.role_permissions if rp.permission
            }

        return UserEntity(
            id=self.id,
            name=self.name,
            email=self.email,
            phone_number=self.phone_number,
            status=self.status,
            avatar_url=self.avatar_url,
            discord_id=self.discord_id,
            zalo_id=self.zalo_id,
            zalo_bot_id=self.zalo_bot_id,
            zalo_bind_code=self.zalo_bind_code,
            role_id=self.role_id,
            account_id=self.account_id,
            role_name=self.role.name if self.role else None,
            permissions=permissions,
            created_at=self.created_at, # type: ignore
            updated_at=self.updated_at, # type: ignore
            created_by=self.created_by,
            updated_by=self.updated_by, # type: ignore
            is_deleted=self.is_deleted, # type: ignore
        )

    @classmethod
    def from_entity(cls, entity: UserEntity) -> UserModel:
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            phone_number=entity.phone_number,
            status=entity.status,
            avatar_url=entity.avatar_url,
            discord_id=entity.discord_id,
            zalo_id=entity.zalo_id,
            zalo_bot_id=entity.zalo_bot_id,
            zalo_bind_code=entity.zalo_bind_code,
            role_id=entity.role_id,
            account_id=entity.account_id,
        )

# Fix circular dependencies
from app.violation.infrastructure.model import ViolationModel  # noqa: E402
UserModel.model_rebuild()  # type: ignore
