"""
Violation Repository — data access layer.

Uses flush() instead of commit(). Session commits at middleware level.
Mapping delegated to ViolationModel.to_entity() / .from_entity().
"""

from app.violation.domain.entity import Violation
from app.violation.infrastructure.model import ViolationModel
from app.shared.infrastructure.base_repository import BaseRepository
from sqlalchemy import desc, extract
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select
from datetime import datetime, date, time
from typing import List, Optional, Any, cast


class ViolationRepository(BaseRepository[ViolationModel, Violation]):
    """Concrete repository using BaseRepository logic."""

    def __init__(self, session: Session):
        super().__init__(session, ViolationModel)

    def get_all(
        self,
        query_support: Optional[Any] = None,
        deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Violation]:
        """Override get_all to include default relations and support skip/limit if no query_support."""
        statement = select(ViolationModel).where(ViolationModel.is_deleted == deleted)

        # Default includes
        statement = statement.options(
            joinedload(cast(Any, ViolationModel.user)),
            joinedload(cast(Any, ViolationModel.creator_rel)),
            joinedload(cast(Any, ViolationModel.updater_rel)),
        )

        if query_support:
            from app.shared.domain.query_support import apply_query_support
            statement = apply_query_support(statement, ViolationModel, query_support)
        else:
            statement = statement.order_by(desc(cast(Any, ViolationModel.created_at)))
            statement = statement.offset(skip).limit(limit)

        return [m.to_entity() for m in self.session.exec(statement).unique().all()]

    def get_by_month(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> List[Violation]:
        """Get violations filtered by month/year/user."""
        statement = select(ViolationModel).where(ViolationModel.is_deleted == False)  # noqa: E712
        
        if user_id:
            statement = statement.where(ViolationModel.user_id == user_id)
        if month is not None:
            statement = statement.where(extract("month", cast(Any, ViolationModel.date)) == month)
        if year is not None:
            statement = statement.where(extract("year", cast(Any, ViolationModel.date)) == year)
            
        statement = statement.options(
            joinedload(cast(Any, ViolationModel.user)),
            joinedload(cast(Any, ViolationModel.creator_rel)),
            joinedload(cast(Any, ViolationModel.updater_rel)),
        ).order_by(desc(cast(Any, ViolationModel.date)))
        
        return [m.to_entity() for m in self.session.exec(statement).unique().all()]

    def get_by_date(self, target_date: date) -> List[Violation]:
        """Get all violations on a specific date (accepts date or datetime)."""
        # Tránh lỗi type hint nếu target_date là datetime
        d = target_date.date() if isinstance(target_date, datetime) else target_date
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)
        
        statement = (
            select(ViolationModel)
            .where(
                ViolationModel.is_deleted == False,  # noqa: E712
                ViolationModel.date >= start,
                ViolationModel.date <= end,
            )
            .options(
                joinedload(cast(Any, ViolationModel.user)),
                joinedload(cast(Any, ViolationModel.creator_rel)),
                joinedload(cast(Any, ViolationModel.updater_rel)),
            )
        )
        return [m.to_entity() for m in self.session.exec(statement).unique().all()]

    def save(self, entity: Violation) -> Violation:
        """Compatibility save method."""
        if entity.id:
            return self.update(entity)
        return self.add(entity)
