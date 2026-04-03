from datetime import date, datetime, time
from typing import Any, List, Optional, cast
from app.shared.domain.query_support import (FilterCriterion, FilterOperator)
from app.shared.application.query_support_utils import build_query_support

from app.core.context import get_current_user_id
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.events import (PermissionRequestCreated,
                                                  PermissionRequestUpdated)
from app.permission_request.domain.repository import \
  PermissionRequestRepository
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.schemas import PermissionRequestUpdate
from app.shared.domain.event_bus import EventBus, DomainEvent
from fastapi import HTTPException


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
        filters = []
        if user_id:
            filters.append(FilterCriterion(field="created_by", operator=FilterOperator.EQ, value=user_id))
        if month:
            filters.append(FilterCriterion(field="date", operator=FilterOperator.MONTH_EQ, value=month))
        if year:
            filters.append(FilterCriterion(field="date", operator=FilterOperator.YEAR_EQ, value=year))

        qs = build_query_support(skip=skip, limit=limit, filters=filters)
        return self.repo.get_all(query_support=qs, deleted=deleted)


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
        note: str,
        homework_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        start_time: Optional[time] = None,
        user_id: Optional[int] = None,
    ) -> PermissionRequest:
        current_user_id = user_id or get_current_user_id()

        # Combine date and time to create a datetime for the Domain Entity
        full_datetime: Optional[datetime] = None
        if start_time:
            full_datetime = datetime.combine(date, start_time)

        request = PermissionRequest(
            user_id=current_user_id,
            category=category,
            date=date,
            note=note,
            homework_id=homework_id,
            meeting_id=meeting_id,
            start_time=full_datetime
        )

        saved = self.repo.save(request)

        # Publish event for (1) Notification and (2) Violation checking
        await self.event_bus.publish(
            cast(DomainEvent, PermissionRequestCreated(
                request_id=cast(int, saved.id),
                user_id=cast(int, saved.user_id),
                category=saved.category,
                date=saved.date,
                note=saved.note,
            ))
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
        if data.note:
            request.note = data.note
        if data.homework_id:
            request.homework_id = data.homework_id
        if data.meeting_id:
            request.meeting_id = data.meeting_id
        if data.start_time:
            # combine updated time with current request date
            request.start_time = datetime.combine(request.date, data.start_time)

        saved = self.repo.save(request)

        await self.event_bus.publish(cast(DomainEvent, PermissionRequestUpdated(request_id=cast(int, saved.id))))
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
        request = self.repo.get_by_id(request_id)
        if request:
            self.repo.restore(request)
            return True
        return False


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
