from typing import List, Optional

from app.bonus_point.application.dtos import BonusPointCreate, BonusPointUpdate
from app.bonus_point.domain.entity import BonusPoint
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.event_bus import EventBus


class GetBonusPointsUseCase:
    def __init__(self, repository: BonusPointRepository):
        self.repository = repository

    def execute(
        self,
        user_id: Optional[int] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        deleted: bool = False,
    ) -> List[BonusPoint]:
        filters = []
        if user_id:
            filters.append(FilterCriterion(field="user_id", operator=FilterOperator.EQ, value=user_id))
        if month:
            filters.append(FilterCriterion(field="date", operator=FilterOperator.MONTH_EQ, value=month))
        if year:
            filters.append(FilterCriterion(field="date", operator=FilterOperator.YEAR_EQ, value=year))
            
        qs = build_query_support(skip=skip, limit=limit, filters=filters)
        return self.repository.get_all(query_support=qs, deleted=deleted)


class CreateBonusPointsUseCase:
    def __init__(
        self,
        repository: BonusPointRepository,
        event_bus: Optional[EventBus] = None,
    ):
        self.repository = repository
        self.event_bus = event_bus

    def execute(self, data: BonusPointCreate) -> List[BonusPoint]:
        created_items = []

        # We bypass model_dump validation temporarily or dump base properties
        for user_id in data.user_ids:
            entity = BonusPoint(
                points=data.points,
                reason=data.reason,
                date=data.date,
                user_id=user_id,
            )
            created = self.repository.add(entity)
            created_items.append(created)

        # Emit events after successful transaction commit
        # (Could add event here if necessary, as per clean architecture rules)

        return created_items


class UpdateBonusPointUseCase:
    def __init__(
        self,
        repository: BonusPointRepository,
        event_bus: Optional[EventBus] = None,
    ):
        self.repository = repository
        self.event_bus = event_bus

    def execute(
        self,
        entity_id: int,
        data: BonusPointUpdate,
    ) -> Optional[BonusPoint]:
        entity = self.repository.get_by_id(entity_id)
        if not entity:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        updated = self.repository.update_entity(entity)

        return updated


class DeleteBonusPointUseCase:
    def __init__(self, repository: BonusPointRepository):
        self.repository = repository

    def execute(self, entity_id: int) -> bool:
        return self.repository.delete_entity(entity_id)


class RestoreBonusPointUseCase:
    def __init__(self, repository: BonusPointRepository):
        self.repository = repository

    def execute(self, entity_id: int) -> Optional[BonusPoint]:
        return self.repository.restore_entity(entity_id)
