from datetime import datetime
from typing import List, Optional, cast
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.shared.application.query_support_utils import build_query_support

from app.core.context import get_current_user_id
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.events import (
    PermissionRequestCreated,
    PermissionRequestUpdated,
)
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.homework.infrastructure.repository import HomeworkRepository
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
        category: Optional[RequestCategory] = None,
        skip: int = 0,
        limit: int = 100,
        deleted: bool = False,
    ) -> List[PermissionRequest]:
        filters = []
        if user_id:
            filters.append(
                FilterCriterion(
                    field="created_by", operator=FilterOperator.EQ, value=user_id
                )
            )
        if month:
            filters.append(
                FilterCriterion(
                    field="created_at", operator=FilterOperator.MONTH_EQ, value=month
                )
            )
        if year:
            filters.append(
                FilterCriterion(
                    field="created_at", operator=FilterOperator.YEAR_EQ, value=year
                )
            )
        if category:
            filters.append(
                FilterCriterion(
                    field="category", operator=FilterOperator.EQ, value=category
                )
            )

        qs = build_query_support(
            skip=skip,
            limit=limit,
            sort_by="created_at",
            descending=True,
            filters=filters,
        )
        return self.repo.get_all(query_support=qs, deleted=deleted)


class CreatePermissionRequestUseCase:
    """Tạo yêu cầu xin phép mới và phát sự kiện"""

    def __init__(
        self,
        repo: PermissionRequestRepository,
        homework_repo: HomeworkRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repo = repo
        self.homework_repo = homework_repo
        self.event_bus = event_bus

    async def execute(
        self,
        category: RequestCategory,
        note: str,
        homework_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        user_id: Optional[int] = None,
    ) -> PermissionRequest:
        current_user_id = user_id or get_current_user_id()

        request = PermissionRequest(
            user_id=current_user_id,
            category=category,
            note=note,
            homework_id=homework_id,
            meeting_id=meeting_id,
            start_time=start_time,
        )

        # Validation for POSTPONE (Homework delay)
        if category == RequestCategory.POSTPONE:
            if not homework_id:
                raise HTTPException(status_code=400, detail="Vui lòng chọn bài tập cần hoãn")
            
            homework = self.homework_repo.get_by_id(homework_id)
            if not homework:
                raise HTTPException(status_code=404, detail="Không tìm thấy bài tập")
            request.validate_postpone(homework)


        saved = self.repo.save(request)

        # Publish event for (1) Notification and (2) Violation checking
        await self.event_bus.publish(
            cast(
                DomainEvent,
                PermissionRequestCreated(
                    request_id=cast(int, saved.id),
                    user_id=cast(int, saved.user_id),
                    category=saved.category,
                    note=saved.note,
                    start_time=saved.start_time,
                ),
            )
        )

        return saved


class UpdatePermissionRequestUseCase:
    """Cập nhật nội dung yêu cầu xin phép"""

    def __init__(
        self,
        repo: PermissionRequestRepository,
        homework_repo: HomeworkRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repo = repo
        self.homework_repo = homework_repo
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
        if data.note:
            request.note = data.note
        if data.homework_id:
            request.homework_id = data.homework_id
        if data.meeting_id:
            request.meeting_id = data.meeting_id
        if data.start_time:
            request.start_time = data.start_time

        # Re-validate if POSTPONE
        if request.category == RequestCategory.POSTPONE:
            if not request.homework_id:
                 raise HTTPException(status_code=400, detail="Vui lòng chọn bài tập cần hoãn")
            
            homework = self.homework_repo.get_by_id(request.homework_id)
            if not homework:
                raise HTTPException(status_code=404, detail="Không tìm thấy bài tập")
            
            request.validate_postpone(homework)
      

        saved = self.repo.save(request)

        await self.event_bus.publish(
            cast(DomainEvent, PermissionRequestUpdated(request_id=cast(int, saved.id)))
        )
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
