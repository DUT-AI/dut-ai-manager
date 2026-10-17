from app.bonus_point.domain.entity import BonusPoint
from app.bonus_point.infrastructure.repository import BonusPointRepository


class RestoreBonusPointUseCase:
    def __init__(self, repository: BonusPointRepository):
        self.repository = repository

    def execute(self, entity_id: int) -> BonusPoint | None:
        return self.repository.restore_entity(entity_id)
