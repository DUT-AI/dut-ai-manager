from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from app.models.base import TimestampMixin
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class ParticipantStatus(str, Enum):
    """Participant status enum"""

    NOT_JOINED = "chưa tham gia"
    JOINED = "đã checkin"


class MeetingParticipant(TimestampMixin, table=True):
    """Meeting Participant model"""

    __tablename__ = "meeting_participants"

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meetings.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    check_in_at: Optional[datetime] = Field(default=None)
    status: ParticipantStatus = Field(default=ParticipantStatus.NOT_JOINED)
    link_image: Optional[str] = Field(default=None, max_length=500)

    # Relationships
    meeting: "Meeting" = Relationship(back_populates="participants")
    user: "User" = Relationship(
        back_populates="meeting_participations",
        sa_relationship_kwargs={"foreign_keys": "[MeetingParticipant.user_id]"},
    )

    @property
    def user_name(self) -> str:
        return self.user.name if self.user else ""

    @property
    def user_avatar(self) -> Optional[str]:
        return self.user.avatar_url if self.user else None


class Meeting(TimestampMixin, table=True):
    """Meeting model"""

    __tablename__ = "meetings"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    content: Optional[str] = Field(default=None, max_length=1000)
    start_time: datetime = Field(index=True)
    end_time: datetime = Field(index=True)
    require_check_in: bool = Field(default=True)

    # Relationships
    participants: List[MeetingParticipant] = Relationship(
        back_populates="meeting",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
