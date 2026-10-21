"""
Duty ORM Models — SQLAlchemy 2.0.
"""

from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.duty.domain.entity import CleaningDuty, DutyStatus
from app.shared.infrastructure.base_model import Base, SQLAlchemyTimestampMixin

if TYPE_CHECKING:
    from app.meeting.infrastructure.model import Meeting
    from app.user.infrastructure.model import UserModel


class CleaningDutyModel(SQLAlchemyTimestampMixin, Base):
    """ORM mapping to 'cleaning_duties' table."""

    __tablename__ = "cleaning_duties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    duty_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    team_id: Mapped[list[int]] = mapped_column(JSONB, nullable=False, default=list)
    meeting_id: Mapped[int | None] = mapped_column(
        ForeignKey("meetings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=DutyStatus.PENDING.value
    )

    # Nội dung công việc trực nhật hôm đó (mặc định + tạo thêm)
    checklist: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

    # Note & Evidence
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_image_urls: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    submitted_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Approval & Rejection fields
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    meeting: Mapped["Meeting | None"] = relationship("Meeting", lazy="joined")
    submitter: Mapped["UserModel | None"] = relationship(
        "UserModel", foreign_keys=[submitted_by], lazy="joined"
    )

    def to_entity(self) -> CleaningDuty:
        """Map ORM model to pure Domain Entity."""
        raw_team_id = self.team_id
        if isinstance(raw_team_id, list):
            parsed_team_id = [int(x) for x in raw_team_id]
        elif raw_team_id is not None:
            parsed_team_id = [int(raw_team_id)]
        else:
            parsed_team_id = []

        meeting_title = self.meeting.title if self.meeting else None
        submitter_name = self.submitter.name if self.submitter else None

        return CleaningDuty(
            id=self.id,
            duty_date=self.duty_date,
            start_time=self.start_time,
            end_time=self.end_time,
            team_id=parsed_team_id,
            meeting_id=self.meeting_id,
            meeting_title=meeting_title,
            status=DutyStatus(self.status),
            checklist=list(self.checklist or []),
            note=self.note,
            evidence_image_urls=list(self.evidence_image_urls or []),
            submitted_by=self.submitted_by,
            submitted_by_name=submitter_name,
            submitted_at=self.submitted_at.replace(tzinfo=None)
            if self.submitted_at
            else None,
            rejection_reason=self.rejection_reason,
            approved_by=self.approved_by,
            approved_at=self.approved_at.replace(tzinfo=None)
            if self.approved_at
            else None,
            rejected_by=self.rejected_by,
            rejected_at=self.rejected_at.replace(tzinfo=None)
            if self.rejected_at
            else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_deleted=self.is_deleted,
        )
