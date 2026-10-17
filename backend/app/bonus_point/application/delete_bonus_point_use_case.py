from app.bonus_point.domain.events import BonusPointDeleted
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.shared.domain.event_bus import EventBus


class DeleteBonusPointUseCase:
    def __init__(
        self,
        repository: BonusPointRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repository = repository
        self.event_bus = event_bus

    async def execute(self, entity_id: int) -> bool:
        entity = self.repository.get_by_id(entity_id)
        if not entity:
            return False

        user_id = entity.user_id
        success = self.repository.delete_entity(entity_id)

        if success and self.event_bus and user_id:
            await self.event_bus.publish(
                BonusPointDeleted(
                    bonus_point_id=entity_id,
                    user_id=user_id,
                )
            )

        return success
