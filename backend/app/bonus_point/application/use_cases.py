from datetime import datetime, timedelta

from app.bonus_point.application.dtos import BonusPointCreate, BonusPointUpdate
from app.bonus_point.domain.entity import BonusPoint
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.meeting.infrastructure.repository import ParticipantRepository
from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.event_bus import EventBus
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.utils.datetime import get_current_utc7_time


class GetBonusPointsUseCase:
    def __init__(self, repository: BonusPointRepository):
        self.repository = repository

    def execute(
        self,
        user_id: int | None = None,
        month: int | None = None,
        year: int | None = None,
        skip: int = 0,
        limit: int = 100,
        deleted: bool = False,
    ) -> list[BonusPoint]:
        filters = []
        if user_id:
            filters.append(
                FilterCriterion(
                    field="user_id", operator=FilterOperator.EQ, value=user_id
                )
            )
        if month:
            filters.append(
                FilterCriterion(
                    field="date", operator=FilterOperator.MONTH_EQ, value=month
                )
            )
        if year:
            filters.append(
                FilterCriterion(
                    field="date", operator=FilterOperator.YEAR_EQ, value=year
                )
            )

        qs = build_query_support(skip=skip, limit=limit, filters=filters)
        return self.repository.get_all(query_support=qs, deleted=deleted)


class CreateBonusPointsUseCase:
    def __init__(
        self,
        repository: BonusPointRepository,
        event_bus: EventBus | None = None,
    ):
        self.repository = repository
        self.event_bus = event_bus

    def execute(self, data: BonusPointCreate) -> list[BonusPoint]:
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
        event_bus: EventBus | None = None,
    ):
        self.repository = repository
        self.event_bus = event_bus

    def execute(
        self,
        entity_id: int,
        data: BonusPointUpdate,
    ) -> BonusPoint | None:
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

    def execute(self, entity_id: int) -> BonusPoint | None:
        return self.repository.restore_entity(entity_id)


class CalculateActivityPointsUseCase:
    def __init__(
        self,
        participant_repo: ParticipantRepository,
        bonus_point_repo: BonusPointRepository,
    ):
        self.participant_repo = participant_repo
        self.bonus_point_repo = bonus_point_repo

    def execute(self, since: datetime | None = None) -> int:

        if since is None:
            since = get_current_utc7_time() - timedelta(hours=1)

        participants = self.participant_repo.get_completed_since(since)

        count = 0
        for p in participants:
            if p.check_in_at and p.check_out_at:
                duration = (p.check_out_at - p.check_in_at).total_seconds()
                hours = duration / 3600
                points = int(round(hours))

                if points > 0:
                    existing = self.bonus_point_repo.get_by_user_and_reason_and_date(
                        user_id=p.user_id,
                        reason="Hoạt động tại CLB",
                        date=p.check_out_at.date(),
                    )

                    if not existing:
                        bonus = BonusPoint(
                            user_id=p.user_id,
                            points=points,
                            reason=f"Hoạt động tại CLB: {hours:.2f} giờ",
                            date=get_current_utc7_time(),
                        )
                        self.bonus_point_repo.add(bonus)
                        count += 1
        return count
