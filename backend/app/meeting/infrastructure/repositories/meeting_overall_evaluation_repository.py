from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.meeting.domain.evaluation import (
    MeetingOverallEvaluation as DomainOverallEvaluation,
)
from app.meeting.infrastructure.model import (
    MeetingOverallEvaluation as ORMOverallEvaluation,
)
from app.shared.infrastructure.base_repository import BaseRepository


class MeetingOverallEvaluationRepository(
    BaseRepository[ORMOverallEvaluation, DomainOverallEvaluation]
):
    """Repository quản lý đánh giá tổng thể buổi học từ Trainer (Quan hệ 1-1)."""

    def __init__(self, session: Session):
        super().__init__(session, ORMOverallEvaluation)

    def save(self, entity: DomainOverallEvaluation) -> DomainOverallEvaluation:
        """Lưu hoặc cập nhật đánh giá tổng thể buổi học (quan hệ 1 - 1)."""
        existing = self.session.scalars(
            select(ORMOverallEvaluation).where(
                ORMOverallEvaluation.meeting_id == entity.meeting_id,
                ORMOverallEvaluation.is_deleted.is_(False),
            )
        ).first()
        if existing:
            existing.scores = [s.model_dump() for s in entity.scores]
            existing.average_score = entity.average_score
            existing.general_feedback = entity.general_feedback
            existing.trainer_id = entity.trainer_id
            orm = existing
        else:
            orm = ORMOverallEvaluation.from_entity(entity)

        self.session.add(orm)
        self.session.flush()
        return orm.to_entity()

    def get_by_meeting_id(self, meeting_id: int) -> DomainOverallEvaluation | None:
        """Lấy đánh giá tổng thể của buổi học kèm thông tin Trainer."""
        stmt = (
            select(ORMOverallEvaluation)
            .where(
                ORMOverallEvaluation.meeting_id == meeting_id,
                ORMOverallEvaluation.is_deleted.is_(False),
            )
            .options(joinedload(ORMOverallEvaluation.trainer))
        )
        orm = self.session.scalars(stmt).first()
        return orm.to_entity() if orm else None

    def exists_for_meeting(self, meeting_id: int) -> bool:
        """Kiểm tra buổi học đã có đánh giá tổng thể từ Trainer hay chưa."""
        stmt = select(func.count(ORMOverallEvaluation.id)).where(
            ORMOverallEvaluation.meeting_id == meeting_id,
            ORMOverallEvaluation.is_deleted.is_(False),
        )
        return (self.session.scalar(stmt) or 0) > 0


__all__ = ["MeetingOverallEvaluationRepository"]
