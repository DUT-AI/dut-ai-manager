from datetime import date
from typing import List, Optional

from app.core.context import get_current_user_id
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.events import (PermissionRequestCreated,
                                                  PermissionRequestUpdated)
from app.permission_request.domain.repository import \
  PermissionRequestRepository
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.event_bus import EventBus
from fastapi import HTTPException, status


class GetPermissionRequestsUseCase:
    """Lấy danh sách các yêu cầu xin phép"""

    def __init__(self, repo: PermissionRequestRepository):
        self.repo = repo

    def execute(
        self,
        user_id: Optional[int] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        deleted: bool = False,
    ) -> List[PermissionRequest]:
        if user_id:
            return self.repo.get_by_user(user_id, month, year, deleted)
        return self.repo.get_all(skip, limit, deleted)


class CreatePermissionRequestUseCase:
    """Tạo yêu cầu xin phép mới và phát sự kiện"""

    def __init__(
        self, repo: PermissionRequestRepository, event_bus: type[EventBus] = EventBus
    ):
        self.repo = repo
        self.event_bus = event_bus

    async def execute(
        self,
        category: RequestCategory,
        date: date,
        reason: str,
        user_id: Optional[int] = None,
    ) -> PermissionRequest:
        current_user_id = user_id or get_current_user_id()

        request = PermissionRequest(
            user_id=current_user_id, category=category, date=date, reason=reason
        )

        saved = self.repo.save(request)

        # Publish event for (1) Notification and (2) Violation checking
        await self.event_bus.publish(
            PermissionRequestCreated(
                request_id=saved.id,
                user_id=saved.user_id,
                category=saved.category,
                date=saved.date,
                reason=saved.reason,
            )
        )

        return saved


class UpdatePermissionRequestUseCase:
    """Cập nhật nội dung yêu cầu xin phép"""

    def __init__(
        self, repo: PermissionRequestRepository, event_bus: type[EventBus] = EventBus
    ):
        self.repo = repo
        self.event_bus = event_bus

    async def execute(
        self, request_id: int, data: "PermissionRequestUpdate"
    ) -> PermissionRequest:
        request = self.repo.get_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")

        # Update fields
        if data.category:
            request.category = data.category
        if data.date:
            request.date = data.date
        if data.reason:
            request.reason = data.reason

        saved = self.repo.save(request)

        await self.event_bus.publish(PermissionRequestUpdated(request_id=saved.id))
        return saved


class DeletePermissionRequestUseCase:
    """Xóa yêu cầu xin phép"""

    def __init__(self, repo: PermissionRequestRepository):
        self.repo = repo

    def execute(self, request_id: int) -> bool:
        return self.repo.delete(request_id)


class RestorePermissionRequestUseCase:
    """Khôi phục yêu cầu xin phép"""

    def __init__(self, repo: PermissionRequestRepository):
        self.repo = repo

    def execute(self, request_id: int) -> bool:
        return self.repo.restore(request_id)


class PermissionRequestUseCases:
    """Đóng gói các Use Cases cho module PermissionRequest"""

    def __init__(
        self,
        get_requests: GetPermissionRequestsUseCase,
        create_request: CreatePermissionRequestUseCase,
        update_request: UpdatePermissionRequestUseCase,
        delete_request: DeletePermissionRequestUseCase,
        restore_request: RestorePermissionRequestUseCase,
        repo: PermissionRequestRepository,
    ):
        self.get_requests = get_requests
        self.create_request = create_request
        self.update_request = update_request
        self.delete_request = delete_request
        self.restore_request = restore_request
        self.repo = repo
