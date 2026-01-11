from typing import List, Optional

from app.api.v1.repositories import BonusPointRepository
from app.models import BonusPoint
from app.schemas.activity import BonusPointCreate, BonusPointUpdate


class BonusPointService:
    def __init__(self, repository: BonusPointRepository):
        self.repository = repository

    def get_all(self, skip: int = 0, limit: int = 100) -> List[BonusPoint]:
        return self.repository.get_all(skip=skip, limit=limit)

    def get(
        self, month: Optional[int] = None, year: Optional[int] = None, user_id: Optional[int] = None
    ) -> List[BonusPoint]:
        return self.repository.get_by_month(month=month, year=year, user_id=user_id)

    def get_by_user_and_date(self, user_id: int, target_date) -> List[BonusPoint]:
        return self.repository.get_by_user_and_date(user_id, target_date)

    def get_by_date(self, target_date) -> List[BonusPoint]:
        return self.repository.get_by_date(target_date)

    def get_by_id(self, item_id: int) -> Optional[BonusPoint]:
        return self.repository.get_by_id(item_id)

    # ...

    def create(self, data: BonusPointCreate) -> BonusPoint:
        item = BonusPoint(**data.model_dump())
        return self.repository.create(item)

    def update(self, item_id: int, data: BonusPointUpdate) -> Optional[BonusPoint]:
        item = self.repository.get_by_id(item_id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)

        return self.repository.update(item)

    def delete(self, item_id: int) -> bool:
        return self.repository.delete_by_id(item_id)
