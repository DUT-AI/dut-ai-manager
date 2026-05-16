"""
User ORM Model — SQLAlchemy 2.0, infrastructure layer.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy import (
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin
from app.user.domain.entity import UserEntity, UserStatus

if TYPE_CHECKING:
    from app.auth.infrastructure.model import AccountModel
    from app.bonus_point.infrastructure.model import BonusPointModel
    from app.meeting.infrastructure.model import MeetingParticipant
    from app.rbac.infrastructure.model import RoleModel
    from app.team.infrastructure.model import TeamMemberModel
    from app.violation.infrastructure.model import ViolationModel


class UserModel(SQLAlchemyTimestampMixin, Base):
    """ORM model — maps to 'users' table."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(20), default=None)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, native_enum=False, length=50), default=UserStatus.ACTIVE
    )
    discord_id: Mapped[str | None] = mapped_column(
        String(255), default=None, index=True
    )
    check_in_card_code: Mapped[str | None] = mapped_column(
        String(64), default=None, unique=True, index=True
    )
    zalo_id: Mapped[str | None] = mapped_column(String(255), default=None, index=True)
    zalo_bot_id: Mapped[str | None] = mapped_column(
        String(255), default=None, index=True
    )
    zalo_bind_code: Mapped[str | None] = mapped_column(
        String(10), default=None, index=True
    )
    avatar_url: Mapped[str | None] = mapped_column(default=None)

    # Foreign keys
    role_id: Mapped[int | None] = mapped_column(
        ForeignKey("roles.id"), default=None, index=True
    )

    # Relationships
    role: Mapped["RoleModel | None"] = relationship(
        back_populates="users",
        foreign_keys=[role_id],
    )
    account: Mapped["AccountModel | None"] = relationship(
        back_populates="user",
        foreign_keys="[AccountModel.user_id]",
    )
    violations: Mapped[list["ViolationModel"]] = relationship(
        back_populates="user",
        foreign_keys="[ViolationModel.user_id]",
    )
    team_members: Mapped[list["TeamMemberModel"]] = relationship(
        back_populates="user",
        foreign_keys="[TeamMemberModel.user_id]",
    )
    meeting_participations: Mapped[list["MeetingParticipant"]] = relationship(
        back_populates="user",
        foreign_keys="[MeetingParticipant.user_id]",
    )
    bonus_points: Mapped[list["BonusPointModel"]] = relationship(
        back_populates="user",
        foreign_keys="[BonusPointModel.user_id]",
    )

    def to_entity(self) -> UserEntity:
        """ORM Model → Domain Entity."""
        # Calculate permissions only if relations are loaded to avoid N+1
        permissions = set()
        role_name = None

        if "role" in self.__dict__ and self.role:
            role_name = self.role.name

            # Check if nested role_permissions is also loaded
            if "role_permissions" in self.role.__dict__:
                permissions = {
                    rp.permission.name
                    for rp in self.role.role_permissions
                    if "permission" in rp.__dict__ and rp.permission
                }

        return UserEntity(
            id=self.id,
            name=self.name,
            email=self.email,
            phone_number=self.phone_number,
            status=self.status,
            avatar_url=self.avatar_url,
            discord_id=self.discord_id,
            check_in_card_code=self.check_in_card_code,
            zalo_id=self.zalo_id,
            zalo_bot_id=self.zalo_bot_id,
            zalo_bind_code=self.zalo_bind_code,
            role_id=self.role_id,
            role_name=role_name,
            permissions=permissions,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: Any) -> "UserModel":
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            phone_number=entity.phone_number,
            status=entity.status,
            avatar_url=entity.avatar_url,
            discord_id=entity.discord_id,
            check_in_card_code=entity.check_in_card_code,
            zalo_id=entity.zalo_id,
            zalo_bot_id=entity.zalo_bot_id,
            zalo_bind_code=entity.zalo_bind_code,
            role_id=entity.role_id,
        )
