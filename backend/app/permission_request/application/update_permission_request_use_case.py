from typing import cast

from fastapi import HTTPException

from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.events import PermissionRequestUpdated
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.permission_request.schemas import PermissionRequestUpdate
from app.shared.domain.event_bus import DomainEvent, EventBus


class UpdatePermissionRequestUseCase:
    """Cập nhật nội dung (lý do) yêu cầu xin phép."""

    def __init__(
        self,
        repo: PermissionRequestRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.repo = repo
        self.event_bus = event_bus

    async def execute(
        self, request_id: int, data: PermissionRequestUpdate
    ) -> PermissionRequest:
        request = self.repo.get_by_id(request_id)
        if not request:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy yêu cầu xin phép"
            )

        # Nghiệp vụ: Không cho phép đổi loại đơn hoặc mục tiêu liên kết sau khi đã tạo
        if data.category is not None and data.category != request.category:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Không thể thay đổi loại đơn sau khi đã tạo. "
                    "Vui lòng hủy đơn và tạo mới."
                ),
            )
        if data.meeting_id is not None and data.meeting_id != request.meeting_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Không thể thay đổi buổi sinh hoạt. Vui lòng hủy đơn và tạo mới."
                ),
            )
        if data.homework_id is not None and data.homework_id != request.homework_id:
            raise HTTPException(
                status_code=400,
                detail=("Không thể thay đổi bài tập. Vui lòng hủy đơn và tạo mới."),
            )

        if data.note is not None:
            request.note = data.note

        saved = self.repo.save(request)

        await self.event_bus.publish(
            cast(DomainEvent, PermissionRequestUpdated(request_id=cast(int, saved.id)))
        )
        return saved
