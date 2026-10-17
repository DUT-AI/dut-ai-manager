from app.bonus_point.application.dtos import BonusPointUpdate
from app.bonus_point.domain.entity import BonusPoint
from app.bonus_point.domain.events import BonusPointUpdated
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.shared.domain.event_bus import EventBus


class UpdateBonusPointUseCase:
    def __init__(
        self,
        repository: BonusPointRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repository = repository
        self.event_bus = event_bus

    async def execute(
        self,
        entity_id: int,
        data: BonusPointUpdate,
        current_user_name: str | None = None,
    ) -> BonusPoint | None:
        entity = self.repository.get_by_id(entity_id)
        if not entity:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        updated = self.repository.update_entity(entity)

        if updated and self.event_bus and updated.id and updated.user_id:
            await self.event_bus.publish(
                BonusPointUpdated(
                    bonus_point_id=updated.id,
                    user_id=updated.user_id,
                    points=updated.points,
                    reason=updated.reason,
                    date=updated.date.isoformat(),
                    user_name=updated.owner.name if updated.owner else None,
                    updater_name=current_user_name,
                )
            )

        return updated
