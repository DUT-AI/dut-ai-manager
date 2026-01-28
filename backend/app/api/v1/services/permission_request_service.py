from typing import List, Optional

from app.api.v1.repositories.permission_request_repository import (
    PermissionRequestRepository,
)
from app.api.v1.services.notification_service import NotificationService
from app.api.v1.services.violation_service import ViolationService
from app.core.context import get_current_user_id
from app.models.permission_request import PermissionRequest, RequestCategory
from app.schemas.activity import ViolationCreate
from app.schemas.permission_request import (
    PermissionRequestCreate,
    PermissionRequestUpdate,
)
from app.utils.datetime import get_current_utc7_time


class PermissionRequestService:
    def __init__(
        self,
        repository: PermissionRequestRepository,
        violation_service: ViolationService,
        notification_service: NotificationService,
    ):
        self.repository = repository
        self.violation_service = violation_service
        self.notification_service = notification_service

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> List[PermissionRequest]:
        return self.repository.get_all(skip=skip, limit=limit, deleted=deleted)

    def get_by_id(self, request_id: int) -> Optional[PermissionRequest]:
        return self.repository.get_by_id(request_id)

    def get(
        self, month: int | None = None, year: int | None = None
    ) -> List[PermissionRequest]:
        return self.repository.get_by_month(month=month, year=year)

    def get_by_user(
        self, user_id: int, month: int | None = None, year: int | None = None
    ) -> List[PermissionRequest]:
        return self.repository.get_by_created_by(
            user_id=user_id, month=month, year=year
        )

    def get_by_date(self, target_date) -> List[PermissionRequest]:
        return self.repository.get_by_date(target_date)

    async def create(self, data: PermissionRequestCreate) -> PermissionRequest:
        user_id = get_current_user_id()

        # Check if this is ABSENCE or POSTPONE category
        if data.category in [RequestCategory.ABSENCE, RequestCategory.POSTPONE]:
            month = data.date.month
            year = data.date.year

            # Count existing requests of same category in same month
            existing_count = self.repository.count_by_user_category_month(
                user_id=user_id,
                category=data.category,
                month=month,
                year=year,
            )

            # If already has at least 1, create a violation
            if existing_count >= 1:
                match data.category:
                    case RequestCategory.ABSENCE:
                        category_text = "xin vắng sinh hoạt"
                    case RequestCategory.POSTPONE:
                        category_text = "xin tạm hoãn bài tập"
                    case _:
                        category_text = "Lỗi không xác định được loại yêu cầu"

                await self.violation_service.create(
                    ViolationCreate(
                        user_id=user_id,
                        reason=f"{category_text.capitalize()} lần {existing_count + 1} trong tháng {month}/{year}",
                        date=get_current_utc7_time(),
                    ),
                    is_system=True,
                )

        request = PermissionRequest(**data.model_dump())
        created_request = self.repository.create(request)

        # Send notification
        await self.notification_service.send_permission_request_notification(
            created_request
        )

        return created_request

    def update(
        self, request_id: int, data: PermissionRequestUpdate
    ) -> Optional[PermissionRequest]:
        request = self.repository.get_by_id(request_id)
        if not request:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(request, key, value)

        return self.repository.update(request)

    def delete(self, request_id: int) -> bool:
        return self.repository.delete_by_id(request_id)

    def restore(self, request_id: int) -> Optional[PermissionRequest]:
        return self.repository.restore(request_id)
