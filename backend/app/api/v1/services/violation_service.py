from typing import Optional

from app.api.v1.repositories.violation_repository import ViolationRepository
from app.models import Violation
from app.schemas.activity import ViolationCreate, ViolationUpdate
from fastapi.exceptions import HTTPException


class ViolationService:
    def __init__(self, repository: ViolationRepository):
        self.repository = repository

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Violation]:
        return self.repository.get_all(skip=skip, limit=limit)

    def get_by_user(
        self, month: int | None = None, year: int | None = None
    ) -> list[Violation]:
        return self.repository.get_by_month(month=month, year=year)

    def get_by_user_and_date(self, user_id: int, target_date) -> list[Violation]:
        return self.repository.get_by_user_and_date(user_id, target_date)

    def get_by_date(self, target_date) -> list[Violation]:
        return self.repository.get_by_date(target_date)

    def get_by_id(self, item_id: int) -> Optional[Violation]:
        item = self.repository.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    def create(self, data: ViolationCreate) -> Violation:
        item = Violation(**data.model_dump())
        return self.repository.create(item)

    def update(self, item_id: int, data: ViolationUpdate) -> Optional[Violation]:
        item = self.repository.get_by_id(item_id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)

        return self.repository.update(item)

    def delete(self, item_id: int) -> bool:
        item = self.repository.get_by_id(item_id)
        return self.repository.delete_by_id(item.id)
