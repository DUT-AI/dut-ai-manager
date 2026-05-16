"""
Team ORM Models — SQLAlchemy 2.0, infrastructure layer.
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin
from app.team.domain.entity import Team as TeamEntity
from app.team.domain.entity import TeamMemberInfo

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class TeamMemberModel(SQLAlchemyTimestampMixin, Base):
    """Junction table for Team and User"""

    __tablename__ = "team_members"

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    # Relationships
    team: Mapped["TeamModel"] = relationship(back_populates="team_members")
    user: Mapped["UserModel"] = relationship(
        back_populates="team_members",
        foreign_keys=[user_id],
    )


class TeamModel(SQLAlchemyTimestampMixin, Base):
    """Team model"""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Relationships
    team_members: Mapped[list[TeamMemberModel]] = relationship(back_populates="team")

    def to_entity(self) -> TeamEntity:
        """ORM Model → Domain Entity."""
        members = []
        member_ids = []
        # Support either full relations or just parsing.
        for tm in self.team_members:
            if not tm.is_deleted:
                member_ids.append(tm.user_id)
                if tm.user:
                    members.append(
                        TeamMemberInfo(
                            user_id=tm.user.id,
                            user_name=tm.user.name,
                            email=tm.user.email,
                            user_avatar_url=tm.user.avatar_url,
                        )
                    )

        return TeamEntity(
            id=self.id,
            team_name=self.team_name,
            members=members,
            member_ids=member_ids,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: TeamEntity) -> "TeamModel":
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            team_name=entity.team_name,
        )
