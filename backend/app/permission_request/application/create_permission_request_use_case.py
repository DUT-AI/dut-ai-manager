from datetime import UTC, datetime
from typing import cast

from fastapi import HTTPException

from app.core.context import get_current_user_id
from app.permission_request.application.strategies.registry import (
    PermissionStrategyRegistry,
)
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.events import PermissionRequestCreated
from app.permission_request.domain.payloads import (
    AbsencePayload,
    BasePermissionPayload,
    ChangeMeetingPayload,
    LatePayload,
    OtherPayload,
    PostponePayload,
)
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.domain.event_bus import DomainEvent, EventBus


class CreatePermissionRequestUseCase:
    """Tạo yêu cầu xin phép mới và phát sự kiện (Sử dụng Strategy Pattern)."""

    def __init__(
        self,
        repo: PermissionRequestRepository,
        strategy_registry: PermissionStrategyRegistry,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repo = repo
        self.strategy_registry = strategy_registry
        self.event_bus = event_bus

    @staticmethod
    def _build_absence(meeting_id: int | None) -> AbsencePayload:
        if not meeting_id:
            raise HTTPException(
                status_code=400,
                detail="Vui lòng chọn buổi sinh hoạt cần xin vắng",
            )
        return AbsencePayload(meeting_id=meeting_id)

    @staticmethod
    def _build_late(meeting_id: int | None, start_time: datetime | None) -> LatePayload:
        if not meeting_id:
            raise HTTPException(
                status_code=400,
                detail="Vui lòng chọn buổi sinh hoạt cần xin đi trễ",
            )
        if not start_time:
            raise HTTPException(
                status_code=400,
                detail="Vui lòng chọn thời gian dự kiến đến buổi sinh hoạt",
            )
        return LatePayload(meeting_id=meeting_id, start_time=start_time)

    @staticmethod
    def _build_postpone(
        homework_id: int | None, start_time: datetime | None
    ) -> PostponePayload:
        if not homework_id:
            raise HTTPException(
                status_code=400,
                detail="Vui lòng chọn bài tập cần hoãn",
            )
        if not start_time:
            raise HTTPException(
                status_code=400,
                detail="Vui lòng chọn thời gian gia hạn bài tập",
            )
        return PostponePayload(homework_id=homework_id, start_time=start_time)

    @staticmethod
    def _build_change_meeting(
        meeting_id: int | None,
        old_meeting_id: int | None,
        start_time: datetime | None,
    ) -> ChangeMeetingPayload:
        if not meeting_id:
            raise HTTPException(
                status_code=400,
                detail="Vui lòng chọn buổi họp đích muốn chuyển đến",
            )
        return ChangeMeetingPayload(
            meeting_id=meeting_id,
            old_meeting_id=old_meeting_id,
            start_time=start_time or datetime.now(UTC),
        )

    def _build_payload(
        self,
        category: RequestCategory,
        homework_id: int | None,
        meeting_id: int | None,
        old_meeting_id: int | None,
        start_time: datetime | None,
    ) -> BasePermissionPayload:
        match category:
            case RequestCategory.ABSENCE:
                return self._build_absence(meeting_id)
            case RequestCategory.LATE:
                return self._build_late(meeting_id, start_time)
            case RequestCategory.POSTPONE:
                return self._build_postpone(homework_id, start_time)
            case RequestCategory.CHANGE_MEETING:
                return self._build_change_meeting(
                    meeting_id, old_meeting_id, start_time
                )
            case _:
                return OtherPayload()

    async def execute(
        self,
        category: RequestCategory,
        note: str,
        homework_id: int | None = None,
        meeting_id: int | None = None,
        old_meeting_id: int | None = None,
        start_time: datetime | None = None,
        user_id: int | None = None,
    ) -> PermissionRequest:
        current_user_id = user_id or get_current_user_id()
        if not current_user_id:
            raise HTTPException(
                status_code=401, detail="Chưa xác thực danh tính người dùng"
            )

        payload = self._build_payload(
            category=category,
            homework_id=homework_id,
            meeting_id=meeting_id,
            old_meeting_id=old_meeting_id,
            start_time=start_time,
        )

        request = PermissionRequest(
            user_id=current_user_id,
            note=note,
            payload=payload,
        )

        # 1. Thẩm định nghiệp vụ qua Strategy
        strategy = self.strategy_registry.get(category)
        strategy.validate(request)

        # 2. Lưu vào CSDL
        saved = self.repo.save(request)

        # 3. Thực thi side-effects qua Strategy
        await strategy.on_created(saved, current_user_id)

        # 4. Phát Domain Event PermissionRequestCreated
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
