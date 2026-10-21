"""
Duty Repository — Data Access Layer.
"""

from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.duty.domain.entity import CleaningDuty, DutyStatus
from app.duty.infrastructure.model import CleaningDutyModel


class DutyRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, duty_id: int) -> CleaningDuty | None:
        stmt = select(CleaningDutyModel).where(
            CleaningDutyModel.id == duty_id,
            CleaningDutyModel.is_deleted.is_(False),
        )
        model = self.session.scalars(stmt).first()
        return model.to_entity() if model else None

    def get_by_meeting_id(self, meeting_id: int) -> list[CleaningDuty]:
        stmt = (
            select(CleaningDutyModel)
            .where(
                CleaningDutyModel.meeting_id == meeting_id,
                CleaningDutyModel.is_deleted.is_(False),
            )
            .order_by(CleaningDutyModel.id.asc())
        )
        models = self.session.scalars(stmt).all()
        return [m.to_entity() for m in models]

    def get_by_date_and_team(
        self, duty_date: date, team_id: int | list[int]
    ) -> CleaningDuty | None:
        target_ids = [team_id] if isinstance(team_id, int) else team_id
        stmt = select(CleaningDutyModel).where(
            CleaningDutyModel.duty_date == duty_date,
            CleaningDutyModel.is_deleted.is_(False),
        )
        if target_ids:
            if len(target_ids) == 1:
                stmt = stmt.where(CleaningDutyModel.team_id.contains([target_ids[0]]))
            else:
                stmt = stmt.where(
                    or_(*[CleaningDutyModel.team_id.contains([t]) for t in target_ids])
                )
        model = self.session.scalars(stmt).first()
        return model.to_entity() if model else None

    def get_duties(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        team_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[CleaningDuty], int]:
        stmt = select(CleaningDutyModel).where(CleaningDutyModel.is_deleted.is_(False))

        if start_date:
            stmt = stmt.where(CleaningDutyModel.duty_date >= start_date)
        if end_date:
            stmt = stmt.where(CleaningDutyModel.duty_date <= end_date)
        if team_id:
            stmt = stmt.where(CleaningDutyModel.team_id.contains([team_id]))
        # Tab lịch sử CHỈ hiển thị các ca COMPLETED, VIOLATED, CANCELLED (loại trừ PENDING, AWAITING_APPROVAL)
        if status:
            stmt = stmt.where(CleaningDutyModel.status == status)
        else:
            stmt = stmt.where(
                CleaningDutyModel.status.in_(
                    [
                        DutyStatus.COMPLETED.value,
                        DutyStatus.VIOLATED.value,
                        DutyStatus.CANCELLED.value,
                    ]
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.scalar(count_stmt) or 0

        # Pagination & ordering (newest date first)
        stmt = (
            stmt.order_by(
                CleaningDutyModel.duty_date.desc(), CleaningDutyModel.id.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        models = self.session.scalars(stmt).all()
        return [m.to_entity() for m in models], total

    def get_pending_duties_for_date(self, target_date: date) -> list[CleaningDuty]:
        """
        Lấy các ca trực chưa hoàn thành vào cuối ngày (PENDING hoặc REJECTED).
        AWAITING_APPROVAL (đang chờ duyệt) không bị phạt vì học viên đã nộp đúng hạn.
        """
        stmt = select(CleaningDutyModel).where(
            CleaningDutyModel.duty_date == target_date,
            CleaningDutyModel.status.in_(
                [DutyStatus.PENDING.value, DutyStatus.REJECTED.value]
            ),
            CleaningDutyModel.is_deleted.is_(False),
        )
        models = self.session.scalars(stmt).all()
        return [m.to_entity() for m in models]

    def get_by_date_range(self, start_date: date, end_date: date) -> list[CleaningDuty]:
        stmt = (
            select(CleaningDutyModel)
            .where(
                CleaningDutyModel.duty_date >= start_date,
                CleaningDutyModel.duty_date <= end_date,
                CleaningDutyModel.is_deleted.is_(False),
            )
            .order_by(CleaningDutyModel.duty_date.asc(), CleaningDutyModel.id.asc())
        )
        models = self.session.scalars(stmt).all()
        return [m.to_entity() for m in models]

    def save(self, duty: CleaningDuty) -> CleaningDuty:
        parsed_team_id = (
            duty.team_id
            if isinstance(duty.team_id, list)
            else ([duty.team_id] if duty.team_id is not None else [])
        )
        if duty.id:
            model = self.session.get(CleaningDutyModel, duty.id)
            if not model:
                raise ValueError(f"CleaningDuty {duty.id} not found")
            model.duty_date = duty.duty_date
            model.start_time = duty.start_time
            model.end_time = duty.end_time
            model.team_id = parsed_team_id
            model.meeting_id = duty.meeting_id
            model.status = duty.status.value
            model.checklist = duty.checklist
            model.note = duty.note
            model.evidence_image_urls = duty.evidence_image_urls
            model.submitted_by = duty.submitted_by
            model.submitted_at = duty.submitted_at
            model.rejection_reason = duty.rejection_reason
            model.approved_by = duty.approved_by
            model.approved_at = duty.approved_at
            model.rejected_by = duty.rejected_by
            model.rejected_at = duty.rejected_at
            self.session.flush()
            return model.to_entity()
        else:
            model = CleaningDutyModel(
                duty_date=duty.duty_date,
                start_time=duty.start_time,
                end_time=duty.end_time,
                team_id=parsed_team_id,
                meeting_id=duty.meeting_id,
                status=duty.status.value,
                checklist=duty.checklist,
                note=duty.note,
                evidence_image_urls=duty.evidence_image_urls,
                submitted_by=duty.submitted_by,
                submitted_at=duty.submitted_at,
                rejection_reason=duty.rejection_reason,
                approved_by=duty.approved_by,
                approved_at=duty.approved_at,
                rejected_by=duty.rejected_by,
                rejected_at=duty.rejected_at,
            )
            self.session.add(model)
            self.session.flush()
            return model.to_entity()

    def delete(self, duty_id: int) -> bool:
        model = self.session.get(CleaningDutyModel, duty_id)
        if not model or model.is_deleted:
            return False
        model.is_deleted = True
        self.session.flush()
        return True
