"""
Review Duty Use Cases: Approve & Reject.
"""

from datetime import datetime, timezone

from app.duty.application.dtos import DutyResponse
from app.duty.infrastructure.repository import DutyRepository
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import EventBus


class ApproveDutyUseCase:
    """Admin hoặc HR duyệt minh chứng trực nhật -> chuyển thành COMPLETED."""

    def __init__(self, duty_repo: DutyRepository, event_bus: type[EventBus] = EventBus):
        self.duty_repo = duty_repo
        self.event_bus = event_bus

    async def execute(self, duty_id: int, admin_id: int) -> DutyResponse:
        duty = self.duty_repo.get_by_id(duty_id)
        if not duty:
            raise BadRequestException("Không tìm thấy ca trực nhật")

        try:
            duty.approve(
                approved_by=admin_id, approved_at=datetime.now(timezone.utc)
            )
        except ValueError as e:
            raise BadRequestException(str(e))

        saved = self.duty_repo.save(duty)
        return DutyResponse.model_validate(saved)


class RejectDutyUseCase:
    """Admin hoặc HR từ chối minh chứng trực nhật kèm lý do để học viên làm lại."""

    def __init__(self, duty_repo: DutyRepository, event_bus: type[EventBus] = EventBus):
        self.duty_repo = duty_repo
        self.event_bus = event_bus

    async def execute(self, duty_id: int, admin_id: int, reason: str) -> DutyResponse:
        duty = self.duty_repo.get_by_id(duty_id)
        if not duty:
            raise BadRequestException("Không tìm thấy ca trực nhật")

        try:
            duty.reject(
                rejected_by=admin_id,
                rejected_at=datetime.now(timezone.utc),
                reason=reason,
            )
        except ValueError as e:
            raise BadRequestException(str(e))

        saved = self.duty_repo.save(duty)
        return DutyResponse.model_validate(saved)
