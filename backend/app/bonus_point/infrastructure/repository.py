from datetime import date
from typing import Any, List, Optional, cast
from app.bonus_point.domain.entity import BonusPoint
from app.bonus_point.infrastructure.model import BonusPointModel
from app.shared.infrastructure.base_repository import BaseRepository
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select, col
from app.shared.domain.query_support import QuerySupport, apply_query_support


class BonusPointRepository(BaseRepository[BonusPointModel, BonusPoint]):
    """SQLite implementation of the BonusPoint Repository."""

    def __init__(self, session: Session):
        super().__init__(session, BonusPointModel)

    def get_all_entities(
        self, query_support: Optional[QuerySupport] = None, deleted: bool = False
    ) -> List[BonusPoint]:
        return self.get_all(query_support=query_support, deleted=deleted)

    def update(self, entity: BonusPoint) -> BonusPoint:
        return super().update(entity)

    def update_entity(self, entity: BonusPoint) -> BonusPoint:
        return self.update(entity)

    def delete_entity(self, id: int) -> bool:
        entity = self.get_by_id(id)
        if entity:
            self.soft_delete(entity)
            return True
        return False

    def restore_entity(self, id: int) -> BonusPoint:
        entity = self.get_by_id(id)
        if entity:
            return self.restore(entity)
        raise ValueError(f"Bonus point with id {id} not found")

    def to_entity(self, model: BonusPointModel) -> BonusPoint:
        """Convert ORM model to Domain Entity."""
        return model.to_entity()

    def from_entity(self, entity: BonusPoint) -> BonusPointModel:
        """Convert Domain Entity to ORM model."""
        return BonusPointModel.from_entity(entity)

    def get_all(
        self, query_support: Optional[QuerySupport] = None, deleted: bool = False
    ) -> List[BonusPoint]:
        """Override get_all to include necessary relations."""
        statement = select(BonusPointModel)
        statement = statement.where(cast(Any, BonusPointModel.is_deleted).is_(deleted))

        # Always include these relations for bonus points
        statement = statement.options(
            joinedload(cast(Any, BonusPointModel.user)),
            joinedload(cast(Any, BonusPointModel.creator)),
            joinedload(cast(Any, BonusPointModel.updater)),
        )

        if query_support:
            statement = apply_query_support(statement, BonusPointModel, query_support)
        else:
            # Default sorting if no query support provided
            statement = statement.order_by(col(BonusPointModel.created_at).desc())

        models = self.session.exec(statement).all()
        return [self.to_entity(m) for m in models]

    def get_by_date(self, target_date: date) -> List[BonusPoint]:
        """Get bonus points for a specific date."""
        from app.shared.application.query_support_utils import build_query_support
        from app.shared.domain.query_support import FilterCriterion, FilterOperator
        
        qs = build_query_support(
            filters=[FilterCriterion(field="date", operator=FilterOperator.EQ, value=target_date)]
        )
        return self.get_all(query_support=qs)

    def get_by_month(self, month: Optional[int] = None, year: Optional[int] = None) -> List[BonusPoint]:
        """Get bonus points for a specific month/year."""
        from app.shared.application.query_support_utils import build_query_support
        from app.shared.domain.query_support import FilterCriterion, FilterOperator
        
        filters = []
        if month:
            filters.append(FilterCriterion(field="date", operator=FilterOperator.MONTH_EQ, value=month))
        if year:
            filters.append(FilterCriterion(field="date", operator=FilterOperator.YEAR_EQ, value=year))
            
        qs = build_query_support(filters=filters, limit=2000)
        return self.get_all(query_support=qs)

    def get_by_user_id(
        self, user_id: int, month: Optional[int] = None, year: Optional[int] = None
    ) -> List[BonusPoint]:
        """Get bonus points for a specific user, optionally filtered by month/year."""
        from app.shared.application.query_support_utils import build_query_support
        from app.shared.domain.query_support import FilterCriterion, FilterOperator
        
        filters = [FilterCriterion(field="user_id", operator=FilterOperator.EQ, value=user_id)]
        if month:
            filters.append(FilterCriterion(field="date", operator=FilterOperator.MONTH_EQ, value=month))
        if year:
            filters.append(FilterCriterion(field="date", operator=FilterOperator.YEAR_EQ, value=year))
        
        qs = build_query_support(filters=filters, limit=1000)
        return self.get_all(query_support=qs)

    def get_by_user_and_reason_and_date(
        self, user_id: int, reason: str, date: date
    ) -> Optional[BonusPoint]:
        """Get a single bonus point by user, reason substring, and date."""
        from sqlalchemy import func
        from app.shared.application.query_support_utils import build_query_support
        from app.shared.domain.query_support import FilterCriterion, FilterOperator

        filters = [
            FilterCriterion(field="user_id", operator=FilterOperator.EQ, value=user_id),
            FilterCriterion(field="date", operator=FilterOperator.EQ, value=date),
        ]
        qs = build_query_support(filters=filters, limit=1)
        results = self.get_all(query_support=qs)

        for bp in results:
            if reason in bp.reason:
                return bp
        return None
