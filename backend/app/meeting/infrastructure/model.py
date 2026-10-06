"""
Meeting ORM Models — SQLAlchemy 2.0, infrastructure layer.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.meeting.domain.entity import (
    EvaluationScoreItem,
    UserRef,
)
from app.meeting.domain.entity import Meeting as MeetingEntity
from app.meeting.domain.entity import (
    MeetingEvaluation as MeetingEvaluationEntity,
)
from app.meeting.domain.entity import MeetingParticipant as MeetingParticipantEntity
from app.meeting.domain.value_objects import EvaluationType, ParticipantStatus
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin
from app.utils.datetime import get_current_utc7_time

if TYPE_CHECKING:
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
    enable_evaluation: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluation_deadline: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    participants: Mapped[list["MeetingParticipant"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
    )
    evaluations: Mapped[list["MeetingEvaluation"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
    )
    creator: Mapped["UserModel | None"] = relationship(
        "UserModel",
        foreign_keys="Meeting.created_by",
        primaryjoin="Meeting.created_by == UserModel.id",
    )

    def to_entity(self) -> MeetingEntity:
        creator_ref = None
        if "creator" in self.__dict__ and self.creator:
            creator_ref = UserRef(
                id=self.creator.id,
                name=self.creator.name or f"Trainer #{self.creator.id}",
                avatar_url=self.creator.avatar_url,
            )
        elif self.created_by:
            creator_ref = UserRef(
                id=self.created_by,
                name=f"Trainer #{self.created_by}",
                avatar_url=None,
            )

        participants_list = []
        raw_participants = getattr(self, "participants", None)
        if raw_participants:
            active_participants = [
                p for p in raw_participants if not getattr(p, "is_deleted", False)
            ]
            sorted_participants = sorted(
                active_participants,
                key=lambda p: (
                    getattr(p, "created_at", None) or datetime.min,
                    getattr(p, "id", None) or 0,
                ),
                reverse=True,
            )
            participants_list = [
                p.to_entity()
                for p in sorted_participants
            ]

        return MeetingEntity(
            id=self.id,
            title=self.title,
            content=self.content,
            start_time=self.start_time,
            end_time=self.end_time,
            require_check_in=(
                self.require_check_in if self.require_check_in is not None else True
            ),
            enable_evaluation=(
                self.enable_evaluation if self.enable_evaluation is not None else False
            ),
            participants=participants_list,
            creator=creator_ref,
            created_at=self.created_at or get_current_utc7_time(),
            updated_at=self.updated_at or get_current_utc7_time(),
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted if self.is_deleted is not None else False,
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
            enable_evaluation=entity.enable_evaluation,
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
    client_event_id: Mapped[str | None] = mapped_column(
        String(255), default=None, index=True
    )

    meeting: Mapped[Meeting] = relationship(back_populates="participants")
    user: Mapped["UserModel"] = relationship(
        back_populates="meeting_participations",
        foreign_keys=[user_id],
    )

    def to_entity(self) -> "MeetingParticipantEntity":
        user_ref = None
        if self.user:
            user_ref = UserRef(
                id=self.user.id,
                name=self.user.name or f"User #{self.user.id}",
                avatar_url=self.user.avatar_url,
            )

        return MeetingParticipantEntity(
            id=self.id,
            meeting_id=self.meeting_id,
            user_id=self.user_id or 0,
            check_in_at=self.check_in_at,
            check_out_at=self.check_out_at,
            status=self.status or ParticipantStatus.NOT_JOINED,
            link_image=self.link_image,
            client_event_id=self.client_event_id,
            user=user_ref,
            created_at=self.created_at or get_current_utc7_time(),
            updated_at=self.updated_at or get_current_utc7_time(),
            created_by=self.created_by,
            updated_by=self.updated_by,
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


class MeetingEvaluation(SQLAlchemyTimestampMixin, Base):
    """Bản ghi đánh giá 2 chiều trong Buổi học (ORM Model)"""

    __tablename__ = "meeting_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    evaluation_type: Mapped[str] = mapped_column(String(50))
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    scores: Mapped[list[dict]] = mapped_column(
        postgresql.JSONB(astext_type=String()), default=list
    )
    average_score: Mapped[float] = mapped_column(Float, default=0.0)
    feedback_text: Mapped[str | None] = mapped_column(String(2000), default=None)

    meeting: Mapped[Meeting] = relationship(back_populates="evaluations")
    reviewer: Mapped["UserModel"] = relationship(foreign_keys=[reviewer_id])
    target_user: Mapped["UserModel"] = relationship(foreign_keys=[target_user_id])

    def to_entity(self) -> "MeetingEvaluationEntity":
        reviewer_ref = None
        if self.reviewer and not self.is_anonymous:
            reviewer_ref = UserRef(
                id=self.reviewer.id or 0,
                name=self.reviewer.name or "",
                avatar_url=self.reviewer.avatar_url,
            )

        target_ref = None
        if self.target_user:
            target_ref = UserRef(
                id=self.target_user.id or 0,
                name=self.target_user.name or "",
                avatar_url=self.target_user.avatar_url,
            )

        score_items = [
            EvaluationScoreItem(
                criteria_code=item.get("criteria_code", ""),
                score=item.get("score", 0),
            )
            for item in (self.scores or [])
        ]

        return MeetingEvaluationEntity(
            id=self.id,
            meeting_id=self.meeting_id,
            reviewer_id=self.reviewer_id,
            target_user_id=self.target_user_id,
            evaluation_type=EvaluationType(self.evaluation_type),
            is_anonymous=self.is_anonymous,
            scores=score_items,
            average_score=self.average_score,
            feedback_text=self.feedback_text,
            reviewer=reviewer_ref,
            target_user=target_ref,
            created_at=self.created_at or get_current_utc7_time(),
            updated_at=self.updated_at or get_current_utc7_time(),
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted if self.is_deleted is not None else False,
        )

    @classmethod
    def from_entity(cls, entity: "MeetingEvaluationEntity") -> "MeetingEvaluation":
        return cls(
            id=entity.id,
            meeting_id=entity.meeting_id,
            reviewer_id=entity.reviewer_id,
            target_user_id=entity.target_user_id,
            evaluation_type=entity.evaluation_type.value
            if hasattr(entity.evaluation_type, "value")
            else str(entity.evaluation_type),
            is_anonymous=entity.is_anonymous,
            scores=[s.model_dump() for s in entity.scores],
            average_score=entity.average_score,
            feedback_text=entity.feedback_text,
        )
