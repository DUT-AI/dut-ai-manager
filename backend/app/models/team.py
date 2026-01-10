from typing import TYPE_CHECKING, List, Optional
from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class TeamMember(TimestampMixin, table=True):
    """Junction table for Team and User"""

    __tablename__ = "team_members"

    team_id: int = Field(foreign_key="teams.id", primary_key=True)
    user_id: int = Field(foreign_key="users.id", primary_key=True)

    # Relationships
    team: "Team" = Relationship(back_populates="team_members")
    user: "User" = Relationship(
        back_populates="team_members",
        sa_relationship_kwargs={"foreign_keys": "[TeamMember.user_id]"},
    )


class Team(TimestampMixin, table=True):
    """Team model"""

    __tablename__ = "teams"

    id: Optional[int] = Field(default=None, primary_key=True)
    team_name: str = Field(unique=True, index=True, max_length=255)

    # Relationships
    team_members: List[TeamMember] = Relationship(back_populates="team")

    @property
    def members(self) -> List["User"]:
        return [tm.user for tm in self.team_members if tm.user]
