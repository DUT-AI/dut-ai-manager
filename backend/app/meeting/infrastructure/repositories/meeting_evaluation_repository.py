from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.meeting.domain.evaluation import MeetingEvaluation as DomainEvaluation
from app.meeting.infrastructure.model import MeetingEvaluation as ORMEvaluation
from app.shared.infrastructure.base_repository import BaseRepository


class MeetingEvaluationRepository(BaseRepository[ORMEvaluation, DomainEvaluation]):
    """Repository quản lý các phiếu đánh giá 2 chiều (MeetingEvaluation)"""

    def __init__(self, session: Session):
        super().__init__(session, ORMEvaluation)

    def _to_domain(self, orm: ORMEvaluation) -> DomainEvaluation:
        return orm.to_entity()

    def save(self, entity: DomainEvaluation) -> DomainEvaluation:
        """Lưu hoặc cập nhật phiếu đánh giá (MeetingEvaluation)."""
        if entity.id:
            orm = self.session.get(ORMEvaluation, entity.id)
            if not orm:
                orm = ORMEvaluation.from_entity(entity)
            else:
                orm.scores = [s.model_dump() for s in entity.scores]
                orm.average_score = entity.average_score
                orm.feedback_text = entity.feedback_text
                orm.is_anonymous = entity.is_anonymous
        else:
            orm = ORMEvaluation.from_entity(entity)

        self.session.add(orm)
        self.session.flush()
        return orm.to_entity()

    def get_by_meeting_and_users(
        self, meeting_id: int, reviewer_id: int, target_user_id: int
    ) -> DomainEvaluation | None:
        stmt = (
            select(ORMEvaluation)
            .where(
                ORMEvaluation.meeting_id == meeting_id,
                ORMEvaluation.reviewer_id == reviewer_id,
                ORMEvaluation.target_user_id == target_user_id,
                ORMEvaluation.is_deleted.is_(False),
            )
            .options(
                joinedload(ORMEvaluation.reviewer),
                joinedload(ORMEvaluation.target_user),
            )
        )
        orm = self.session.scalars(stmt).first()
        return self._to_domain(orm) if orm else None

    def get_evaluations_by_meeting(
        self, meeting_id: int, evaluation_type: str | None = None
    ) -> list[DomainEvaluation]:
        stmt = (
            select(ORMEvaluation)
            .where(
                ORMEvaluation.meeting_id == meeting_id,
                ORMEvaluation.is_deleted.is_(False),
            )
            .options(
                joinedload(ORMEvaluation.reviewer),
                joinedload(ORMEvaluation.target_user),
            )
            .order_by(desc(ORMEvaluation.created_at))
        )
        if evaluation_type:
            stmt = stmt.where(ORMEvaluation.evaluation_type == evaluation_type)
        orms = self.session.scalars(stmt).all()
        return [self._to_domain(orm) for orm in orms]

    def get_evaluations_for_user_in_meeting(
        self, meeting_id: int, target_user_id: int
    ) -> list[DomainEvaluation]:
        stmt = (
            select(ORMEvaluation)
            .where(
                ORMEvaluation.meeting_id == meeting_id,
                ORMEvaluation.target_user_id == target_user_id,
                ORMEvaluation.is_deleted.is_(False),
            )
            .options(
                joinedload(ORMEvaluation.reviewer),
                joinedload(ORMEvaluation.target_user),
            )
        )
        orms = self.session.scalars(stmt).all()
        return [self._to_domain(orm) for orm in orms]

    def count_evaluations_by_reviewer(self, meeting_id: int, reviewer_id: int) -> int:
        stmt = select(func.count(ORMEvaluation.id)).where(
            ORMEvaluation.meeting_id == meeting_id,
            ORMEvaluation.reviewer_id == reviewer_id,
            ORMEvaluation.is_deleted.is_(False),
        )
        return self.session.scalar(stmt) or 0


__all__ = ["MeetingEvaluationRepository"]
