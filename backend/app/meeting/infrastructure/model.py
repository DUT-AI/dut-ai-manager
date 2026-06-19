"""
Meeting ORM Models — SQLAlchemy 2.0, infrastructure layer.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.meeting.domain.entity import Meeting as MeetingEntity
from app.meeting.domain.entity import MeetingParticipant as MeetingParticipantEntity
from app.meeting.domain.entity import UserRef
from app.meeting.domain.value_objects import ParticipantStatus
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin
from app.user.infrastructure.model import UserModel


class Meeting(SQLAlchemyTimestampMixin, Base):
    """Buổi họp (ORM Model)"""

    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(String(1000), default=None)
    start_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    require_check_in: Mapped[bool] = mapped_column(Boolean, default=True)

    participants: Mapped[list["MeetingParticipant"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
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

    @classmethod
    def from_entity(cls, entity: MeetingEntity) -> "Meeting":
        return cls(
            id=entity.id,
            title=entity.title,
            content=entity.content,
            start_time=entity.start_time,
            end_time=entity.end_time,
            require_check_in=entity.require_check_in,
        )


class MeetingParticipant(SQLAlchemyTimestampMixin, Base):
    """Bản ghi thành viên tham dự buổi họp (ORM Model)"""

    __tablename__ = "meeting_participants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    status: Mapped[ParticipantStatus] = mapped_column(
        String(50), default=ParticipantStatus.NOT_JOINED
    )
    link_image: Mapped[str | None] = mapped_column(String(500), default=None)
    client_event_id: Mapped[str | None] = mapped_column(String(255), default=None, index=True)

    meeting: Mapped[Meeting] = relationship(back_populates="participants")
    user: Mapped[UserModel] = relationship(
        back_populates="meeting_participations",
        foreign_keys=[user_id],
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
            client_event_id=self.client_event_id,
            user=user_ref,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity: MeetingParticipantEntity) -> "MeetingParticipant":
        return cls(
            id=entity.id,
            meeting_id=entity.meeting_id,
            user_id=entity.user_id,
            check_in_at=entity.check_in_at,
            check_out_at=entity.check_out_at,
            status=entity.status,
            link_image=entity.link_image,
            client_event_id=entity.client_event_id,
        )
