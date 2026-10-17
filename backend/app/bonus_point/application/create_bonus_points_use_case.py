from app.bonus_point.application.dtos import BonusPointCreate
from app.bonus_point.domain.entity import BonusPoint
from app.bonus_point.domain.events import BonusPointCreated
from app.bonus_point.domain.value_objects import infer_bonus_point_type
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.shared.domain.event_bus import EventBus


class CreateBonusPointsUseCase:
    def __init__(
        self,
        repository: BonusPointRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repository = repository
        self.event_bus = event_bus

    async def execute(
        self, data: BonusPointCreate, current_user_name: str | None = None
    ) -> list[BonusPoint]:
        created_items = []
        resolved_type = data.type or infer_bonus_point_type(data.reason)

        for user_id in data.user_ids:
            entity = BonusPoint(
                points=data.points,
                reason=data.reason,
                date=data.date,
                type=resolved_type,
                user_id=user_id,
            )
            created = self.repository.add(entity)
            created_items.append(created)

            # Publish domain event for notification
            if self.event_bus and created.id and created.user_id:
                await self.event_bus.publish(
                    BonusPointCreated(
                        bonus_point_id=created.id,
                        user_id=created.user_id,
                        points=created.points,
                        reason=created.reason,
                        date=created.date.isoformat(),
                        user_name=created.owner.name if created.owner else None,
                        creator_name=current_user_name,
                    )
                )

        return created_items
