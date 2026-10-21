"""
Toggle Duty Schedule Use Case (for Admin/HR).
"""

from datetime import date, time
from typing import cast

from app.duty.application.dtos import DutyResponse
from app.duty.domain.entity import (
    DEFAULT_DUTY_CHECKLIST,
    CleaningDuty,
    DutyStatus,
)
from app.duty.domain.events import DutyScheduled
from app.duty.infrastructure.repository import DutyRepository
from app.meeting.infrastructure.repository import MeetingRepository
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.team.infrastructure.repository import TeamRepository


class ToggleDutyScheduleUseCase:
    """Bật hoặc tắt lịch trực nhật cho một ngày và nhóm cụ thể."""

    def __init__(
        self,
        duty_repo: DutyRepository,
        meeting_repo: MeetingRepository,
        team_repo: TeamRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.duty_repo = duty_repo
        self.meeting_repo = meeting_repo
        self.team_repo = team_repo
        self.event_bus = event_bus

    async def execute(
        self,
        duty_date: date,
        team_id: int | list[int],
        enabled: bool,
        start_time: time | None = None,
        end_time: time | None = None,
        meeting_id: int | None = None,
        checklist: list[dict] | None = None,
        note: str | None = None,
    ) -> DutyResponse | None:
        target_team_ids = [team_id] if isinstance(team_id, int) else team_id
        existing = self.duty_repo.get_by_date_and_team(
            duty_date=duty_date, team_id=target_team_ids
        )

        # Helper để gán tên nhóm
        def populate_team_names(d: CleaningDuty):
            t_ids = d.team_id if isinstance(d.team_id, list) else [d.team_id]
            t_models = [self.team_repo.get_by_id(t) for t in t_ids]
            t_names = [
                (m.team_name if m and m.team_name else f"Team {t}")
                for m, t in zip(t_models, t_ids)
            ]
            d.team_names = t_names
            d.team_name = ", ".join(t_names)

        # Case 1: Tắt lịch trực
        if not enabled:
            if existing and existing.id:
                if existing.status == DutyStatus.COMPLETED:
                    raise BadRequestException(
                        "Ca trực nhật đã hoàn thành nghiệm thu (COMPLETED), không thể hủy bỏ."
                    )
                if existing.status == DutyStatus.AWAITING_APPROVAL:
                    raise BadRequestException(
                        "Ca trực nhật đang chờ Admin/HR duyệt minh chứng (AWAITING APPROVAL), không thể hủy bỏ."
                    )
                # Cả ca tự do lẫn ca meeting: chuyển sang CANCELLED để giữ lại trên giao diện Lịch Tuần với Switch OFF chứ không xóa
                existing.status = DutyStatus.CANCELLED
                self.duty_repo.save(existing)
            return None

        # Case 2: Bật lịch trực
        if existing:
            # Nếu ca trực đang CANCELLED hoặc PENDING và có cập nhật ghi chú hoặc checklist từ Admin/HR
            if existing.status in [DutyStatus.CANCELLED, DutyStatus.PENDING]:
                existing.status = DutyStatus.PENDING
                if start_time is not None:
                    existing.start_time = start_time
                if end_time is not None:
                    existing.end_time = end_time
                if checklist is not None:
                    existing.checklist = checklist
                if note is not None:
                    existing.note = note
                updated = self.duty_repo.save(existing)
                populate_team_names(updated)
                return DutyResponse.model_validate(updated)
            populate_team_names(existing)
            return DutyResponse.model_validate(existing)

        # Dò tìm meeting nếu có (Admin/HR có thể tự tạo lịch trực tự do không bắt buộc phải có meeting)
        matched_meeting_id = meeting_id
        if not matched_meeting_id:
            meetings = self.meeting_repo.get_by_date(duty_date)
            if meetings:
                matched_meeting_id = meetings[0].id

        teams = [self.team_repo.get_by_id(t) for t in target_team_ids]
        team_names = [
            (t.team_name if t and t.team_name else f"Team {t_id}")
            for t, t_id in zip(teams, target_team_ids)
        ]
        combined_name = ", ".join(team_names)

        new_duty = CleaningDuty(
            duty_date=duty_date,
            start_time=start_time,
            end_time=end_time,
            team_id=target_team_ids,
            team_name=combined_name,
            team_names=team_names,
            meeting_id=matched_meeting_id,
            status=DutyStatus.PENDING,
            checklist=checklist
            if checklist is not None
            else [dict(i) for i in DEFAULT_DUTY_CHECKLIST],
            note=note,
        )

        saved = self.duty_repo.save(new_duty)
        assert saved.id is not None
        saved.team_name = combined_name
        saved.team_names = team_names

        # Publish event
        await self.event_bus.publish(
            cast(
                DomainEvent,
                DutyScheduled(
                    duty_id=saved.id,
                    team_id=saved.team_id,
                    team_name=combined_name,
                    duty_date=str(saved.duty_date),
                    meeting_id=saved.meeting_id,
                ),
            )
        )

        return DutyResponse.model_validate(saved)


class BatchCreateDutyUseCase:
    """Tạo lịch trực nhật tự do cho một hoặc nhiều nhóm cùng lúc (tạo duy nhất 1 lịch trực chứa nhiều nhóm)."""

    def __init__(
        self,
        duty_repo: DutyRepository,
        team_repo: TeamRepository,
        event_bus: type[EventBus] = EventBus,
    ):
        self.duty_repo = duty_repo
        self.team_repo = team_repo
        self.event_bus = event_bus

    async def execute(
        self,
        team_ids: list[int],
        duty_date: date,
        start_time: time | None = None,
        end_time: time | None = None,
        checklist: list[dict] | None = None,
        note: str | None = None,
    ) -> list[DutyResponse]:
        target_team_ids = list(dict.fromkeys(team_ids))
        teams = [self.team_repo.get_by_id(t_id) for t_id in target_team_ids]
        team_names = [
            (t.team_name if t and t.team_name else f"Team {t_id}")
            for t, t_id in zip(teams, target_team_ids)
        ]
        combined_name = ", ".join(team_names)

        # Tạo duy nhất 1 ca trực nhật chứa toàn bộ các nhóm phụ trách
        new_duty = CleaningDuty(
            duty_date=duty_date,
            start_time=start_time,
            end_time=end_time,
            team_id=target_team_ids,
            team_name=combined_name,
            team_names=team_names,
            meeting_id=None,
            status=DutyStatus.PENDING,
            checklist=checklist
            if checklist is not None
            else [dict(i) for i in DEFAULT_DUTY_CHECKLIST],
            note=note,
        )
        saved = self.duty_repo.save(new_duty)
        assert saved.id is not None
        saved.team_name = combined_name
        saved.team_names = team_names

        await self.event_bus.publish(
            cast(
                DomainEvent,
                DutyScheduled(
                    duty_id=saved.id,
                    team_id=saved.team_id,
                    team_name=combined_name,
                    duty_date=str(saved.duty_date),
                    meeting_id=None,
                ),
            )
        )

        return [DutyResponse.model_validate(saved)]
