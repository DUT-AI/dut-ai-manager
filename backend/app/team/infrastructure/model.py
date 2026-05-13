"""
Team ORM Models — SQLModel, infrastructure layer.
"""

from typing import TYPE_CHECKING, List, Optional

from app.shared.infrastructure.base_model import TimestampMixin
from app.team.domain.entity import Team as TeamEntity
from app.team.domain.entity import TeamMemberInfo
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class TeamMemberModel(TimestampMixin, table=True):
    """Junction table for Team and User"""

    __tablename__ = "team_members"

    team_id: int = Field(foreign_key="teams.id", primary_key=True)
    user_id: int = Field(foreign_key="users.id", primary_key=True)

    # Relationships
    team: "TeamModel" = Relationship(back_populates="team_members")
    user: "UserModel" = Relationship(
        back_populates="team_members",
        sa_relationship_kwargs={"foreign_keys": "[TeamMemberModel.user_id]"},
    )


class TeamModel(TimestampMixin, table=True):
    """Team model"""

    __tablename__ = "teams"

    id: Optional[int] = Field(default=None, primary_key=True)
    team_name: str = Field(unique=True, index=True, max_length=255)

    # Relationships
    team_members: List[TeamMemberModel] = Relationship(back_populates="team")

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
            created_at=self.created_at,  # type: ignore
            updated_at=self.updated_at,  # type: ignore
            created_by=self.created_by,
            updated_by=self.updated_by,  # type: ignore
            is_deleted=self.is_deleted,  # type: ignore
        )

    @classmethod
    def from_entity(cls, entity: TeamEntity) -> "TeamModel":
        """Domain Entity → ORM Model."""
        return cls(
            id=entity.id,
            team_name=entity.team_name,
        )
