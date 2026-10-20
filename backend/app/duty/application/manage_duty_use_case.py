"""
Manage Duty Use Cases — Update and Delete (Admin/HR).
"""

from typing import cast

from app.duty.application.dtos import DutyResponse, UpdateDutyRequest
from app.duty.domain.entity import DutyStatus
from app.duty.domain.events import DutyUpdated
from app.duty.infrastructure.repository import DutyRepository
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.team.infrastructure.repository import TeamRepository


class UpdateDutyUseCase:
    """Cập nhật thông tin ca trực nhật (checklist, ghi chú phân công, nhóm, ngày)."""

    def __init__(
        self,
        duty_repo: DutyRepository,
        team_repo: TeamRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.duty_repo = duty_repo
        self.team_repo = team_repo
        self.event_bus = event_bus

    async def execute(self, duty_id: int, req: UpdateDutyRequest) -> DutyResponse:
        duty = self.duty_repo.get_by_id(duty_id)
        if not duty:
            raise BadRequestException(
                message="Ca trực nhật không tồn tại", status_code=404
            )

        if req.checklist is not None:
            duty.checklist = req.checklist
        if req.note is not None:
            duty.note = req.note
        if req.duty_date is not None:
            duty.duty_date = req.duty_date
        if req.start_time is not None:
            duty.start_time = req.start_time
        if req.end_time is not None:
            duty.end_time = req.end_time
        if req.team_id is not None:
            t_ids = [req.team_id] if isinstance(req.team_id, int) else req.team_id
            duty.team_id = t_ids
            t_models = [self.team_repo.get_by_id(t) for t in t_ids]
            t_names = [m.team_name for m in t_models if m and m.team_name]
            duty.team_names = t_names
            duty.team_name = ", ".join(t_names)

        saved = self.duty_repo.save(duty)
        if not duty.team_name and duty.team_id:
            t_models = [self.team_repo.get_by_id(t) for t in duty.team_id]
            t_names = [m.team_name for m in t_models if m and m.team_name]
            saved.team_names = t_names
            saved.team_name = ", ".join(t_names)

        is_rescheduled = bool(
            req.duty_date is not None
            or req.start_time is not None
            or req.end_time is not None
        )
        await self.event_bus.publish(
            cast(
                DomainEvent,
                DutyUpdated(
                    duty_id=cast(int, saved.id),
                    team_id=saved.team_id,
                    team_name=saved.team_name or "",
                    duty_date=str(saved.duty_date),
                    meeting_id=saved.meeting_id,
                    is_time_changed=is_rescheduled,
                ),
            )
        )
        return DutyResponse.model_validate(saved)


class DeleteDutyUseCase:
    """Xóa (hủy) một ca trực nhật, chuyển sang trạng thái CANCELLED để lưu vào lịch sử."""

    def __init__(self, duty_repo: DutyRepository):
        self.duty_repo = duty_repo

    async def execute(self, duty_id: int) -> bool:
        duty = self.duty_repo.get_by_id(duty_id)
        if not duty:
            raise BadRequestException(
                message="Ca trực nhật không tồn tại", status_code=404
            )

        if duty.status == DutyStatus.COMPLETED:
            raise BadRequestException(
                "Ca trực nhật đã hoàn thành nghiệm thu (COMPLETED), không thể xóa."
            )
        if duty.status == DutyStatus.AWAITING_APPROVAL:
            raise BadRequestException(
                "Ca trực nhật đang chờ Admin/HR duyệt minh chứng (AWAITING APPROVAL), không thể xóa."
            )

        duty.status = DutyStatus.CANCELLED
        self.duty_repo.save(duty)
        return True


class RestoreDutyUseCase:
    """Hồi phục ca trực nhật đã bị hủy (CANCELLED) trở lại trạng thái PENDING."""

    def __init__(self, duty_repo: DutyRepository):
        self.duty_repo = duty_repo

    async def execute(self, duty_id: int) -> DutyResponse:
        duty = self.duty_repo.get_by_id(duty_id)
        if not duty:
            raise BadRequestException(
                message="Ca trực nhật không tồn tại", status_code=404
            )

        if duty.status != DutyStatus.CANCELLED:
            raise BadRequestException(
                "Chỉ có thể hồi phục ca trực nhật đang ở trạng thái CANCELLED."
            )

        duty.status = DutyStatus.PENDING
        saved = self.duty_repo.save(duty)
        return DutyResponse.model_validate(saved)
