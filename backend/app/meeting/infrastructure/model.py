from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from app.meeting.domain.entity import Meeting as MeetingEntity
from app.meeting.domain.entity import MeetingParticipant as MeetingParticipantEntity
from app.meeting.domain.entity import UserRef
from app.meeting.domain.value_objects import ParticipantStatus
from app.shared.infrastructure.base_model import TimestampMixin
from app.user.infrastructure.model import UserModel
from sqlmodel import Field, Relationship


class Meeting(TimestampMixin, table=True):
    """Buổi họp (ORM Model)"""

    __tablename__ = "meetings"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    content: Optional[str] = Field(default=None, max_length=1000)
    start_time: datetime = Field(index=True)
    end_time: datetime = Field(index=True)
    require_check_in: bool = Field(default=True)

    participants: List["MeetingParticipant"] = Relationship(
        back_populates="meeting",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    def to_entity(self) -> MeetingEntity:
        return MeetingEntity(
            id=self.id,
            title=self.title,
            content=self.content,
            start_time=self.start_time,
            end_time=self.end_time,
            require_check_in=self.require_check_in,
            participants=(
                [p.to_entity() for p in self.participants] if self.participants else []
            ),
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
        )


class MeetingParticipant(TimestampMixin, table=True):
    """Bản ghi thành viên tham dự buổi họp (ORM Model)"""

    __tablename__ = "meeting_participants"

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meetings.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    check_in_at: Optional[datetime] = Field(default=None)
    check_out_at: Optional[datetime] = Field(default=None)
    status: ParticipantStatus = Field(default=ParticipantStatus.NOT_JOINED)
    link_image: Optional[str] = Field(default=None, max_length=500)

    meeting: Meeting = Relationship(back_populates="participants")
    user: UserModel = Relationship(
        back_populates="meeting_participations",
        sa_relationship_kwargs={"foreign_keys": "[MeetingParticipant.user_id]"},
    )

    def to_entity(self) -> "MeetingParticipantEntity":
        user_ref = None
        if self.user:
            user_ref = UserRef(
                id=self.user.id or 0,
                name=self.user.name,
                avatar_url=self.user.avatar_url,
            )

        return MeetingParticipantEntity(
            id=self.id,
            meeting_id=self.meeting_id,
            user_id=self.user_id,
            check_in_at=self.check_in_at,
            check_out_at=self.check_out_at,
            status=self.status,
            link_image=self.link_image,
            user=user_ref,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
