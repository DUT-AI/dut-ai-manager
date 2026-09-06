"""
User ORM Model — SQLAlchemy 2.0, infrastructure layer.
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum as SQLEnum,
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


class UserRoleModel(SQLAlchemyTimestampMixin, Base):
    """Database ORM mapping to 'user_roles' table."""

    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), index=True
    )


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

    # Relationships
    roles: Mapped[list["RoleModel"]] = relationship(
        secondary="user_roles",
        primaryjoin="UserModel.id == UserRoleModel.user_id",
        secondaryjoin="RoleModel.id == UserRoleModel.role_id",
        back_populates="users",
    )
    account: Mapped["AccountModel | None"] = relationship(
        "AccountModel",
        back_populates="user",
        primaryjoin="UserModel.id == AccountModel.user_id",
    )

    violations: Mapped[list["ViolationModel"]] = relationship(
        "ViolationModel",
        back_populates="user",
        primaryjoin="UserModel.id == ViolationModel.user_id",
    )
    team_members: Mapped[list["TeamMemberModel"]] = relationship(
        "TeamMemberModel",
        back_populates="user",
        primaryjoin="UserModel.id == TeamMemberModel.user_id",
    )
    meeting_participations: Mapped[list["MeetingParticipant"]] = relationship(
        "MeetingParticipant",
        back_populates="user",
        primaryjoin="UserModel.id == MeetingParticipant.user_id",
    )
    bonus_points: Mapped[list["BonusPointModel"]] = relationship(
        "BonusPointModel",
        back_populates="user",
        primaryjoin="UserModel.id == BonusPointModel.user_id",
    )

    def to_entity(self) -> UserEntity:
        """ORM Model → Domain Entity."""
        # Calculate permissions only if relations are loaded to avoid N+1
        permissions = set()
        role_names = []
        role_ids = []

        if "roles" in self.__dict__ and self.roles:
            for r in self.roles:
                role_names.append(r.name)
                role_ids.append(r.id)
                if hasattr(r, "role_permissions") and r.role_permissions:
                    for rp in r.role_permissions:
                        if hasattr(rp, "permission") and rp.permission:
                            code = f"{rp.permission.resource}:{rp.permission.action}"
                            permissions.add(code)


        return UserEntity(
            id=self.id,
            name=self.name,
            phone_number=self.phone_number,
            email=self.email,
            status=self.status,
            discord_id=self.discord_id,
            check_in_card_code=self.check_in_card_code,
            zalo_id=self.zalo_id,
            zalo_bot_id=self.zalo_bot_id,
            zalo_bind_code=self.zalo_bind_code,
            avatar_url=self.avatar_url,
            role_ids=role_ids,
            role_names=role_names,
            permissions=list(permissions),
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: UserEntity) -> "UserModel":
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            name=entity.name,
            phone_number=entity.phone_number,
            email=entity.email,
            status=entity.status,
            discord_id=entity.discord_id,
            check_in_card_code=entity.check_in_card_code,
            zalo_id=entity.zalo_id,
            zalo_bot_id=entity.zalo_bot_id,
            zalo_bind_code=entity.zalo_bind_code,
            avatar_url=entity.avatar_url,
        )
