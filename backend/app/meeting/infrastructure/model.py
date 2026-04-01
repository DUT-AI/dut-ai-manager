from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from app.shared.infrastructure.base_model import TimestampMixin
from sqlmodel import Field, Relationship, SQLModel

from ..domain.value_objects import ParticipantStatus

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class MeetingParticipant(TimestampMixin, table=True):
    """Bản ghi thành viên tham dự buổi họp (ORM Model)"""

    __tablename__ = "meeting_participants"

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meetings.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    check_in_at: Optional[datetime] = Field(default=None)
    status: ParticipantStatus = Field(default=ParticipantStatus.NOT_JOINED)
    link_image: Optional[str] = Field(default=None, max_length=500)

    # Relationships
    meeting: "Meeting" = Relationship(back_populates="participants")
    user: "UserModel" = Relationship(
        back_populates="meeting_participations",
        sa_relationship_kwargs={"foreign_keys": "[MeetingParticipant.user_id]"},
    )


class Meeting(TimestampMixin, table=True):
    """Buổi họp (ORM Model)"""

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
