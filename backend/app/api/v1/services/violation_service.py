from app.api.v1.services.notification_service import NotificationService
from app.api.v1.services.user_service import UserService
from typing import Optional

from app.api.v1.repositories.violation_repository import ViolationRepository
from app.models import Violation
from app.schemas.activity import ViolationCreate, ViolationUpdate
from fastapi.exceptions import HTTPException
from loguru import logger


class ViolationService:
    def __init__(
        self,
        repository: ViolationRepository,
        user_service: UserService,
        notification_service: NotificationService,
    ):
        self.repository = repository
        self.user_service = user_service
        self.notification_service = notification_service

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Violation]:
        return self.repository.get_all(skip=skip, limit=limit)

    def get(
        self,
        month: int | None = None,
        year: int | None = None,
        user_id: int | None = None,
    ) -> list[Violation]:
        return self.repository.get_by_month(month=month, year=year, user_id=user_id)

    def get_by_user_and_date(self, user_id: int, target_date) -> list[Violation]:
        return self.repository.get_by_user_and_date(user_id, target_date)

    def get_by_date(self, target_date) -> list[Violation]:
        return self.repository.get_by_date(target_date)

    def get_by_id(self, item_id: int) -> Optional[Violation]:
        item = self.repository.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    async def create(self, data: ViolationCreate, is_system: bool = False) -> Violation:
        item = Violation(**data.model_dump())
        if is_system:
            system_user = self.user_service.get_system()
            item.created_by = system_user.id
            item.updated_by = system_user.id
        logger.debug(f"create violation: {item}")
        created_violation = self.repository.create(item)

        # Send notification
        await self.notification_service.send_violation_notification(created_violation)

        return created_violation

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
