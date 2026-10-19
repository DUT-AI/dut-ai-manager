"""
Check Overdue Duties Use Case (for Daily Scheduled Job at 23:59).
"""

from datetime import date, datetime
from typing import cast
from loguru import logger

from app.duty.domain.entity import DutyStatus
from app.duty.domain.events import DutyViolated
from app.duty.infrastructure.repository import DutyRepository
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import MeetingRepository
from app.shared.domain.event_bus import DomainEvent, EventBus
from app.team.infrastructure.repository import TeamRepository
from app.utils.datetime import get_current_utc7_time
from app.violation.application.create_violation_use_case import CreateViolationUseCase


class CheckOverdueDutiesUseCase:
    """
    Kiểm tra các ca trực nhật trong ngày lúc 23:59.
    Nếu ca trực vẫn PENDING hoặc REJECTED (chưa nộp hoặc bị từ chối và chưa nộp lại),
    tự động phạt những học viên thuộc nhóm trực đã check-in thực tế.
    """

    def __init__(
        self,
        duty_repo: DutyRepository,
        meeting_repo: MeetingRepository,
        team_repo: TeamRepository,
        create_violation_use_case: CreateViolationUseCase,
        event_bus: type[EventBus] = EventBus,
    ):
        self.duty_repo = duty_repo
        self.meeting_repo = meeting_repo
        self.team_repo = team_repo
        self.create_violation_use_case = create_violation_use_case
        self.event_bus = event_bus

    async def execute(self, target_date: date | None = None) -> int:
        if target_date is None:
            target_date = get_current_utc7_time().date()

        pending_duties = self.duty_repo.get_pending_duties_for_date(target_date)
        if not pending_duties:
            logger.info(f"Không có ca trực nhật nào quá hạn trong ngày {target_date}")
            return 0

        date_str = target_date.strftime("%d/%m/%Y")
        violations_count = 0

        for duty in pending_duties:
            assert duty.id is not None

            # Bỏ qua nếu ca trực không ở trạng thái vi phạm
            if duty.status not in (DutyStatus.PENDING, DutyStatus.REJECTED):
                continue

            penalized_user_ids: list[int] = []

            # Lấy thông tin các nhóm trực nhật
            t_ids = duty.team_id if isinstance(duty.team_id, list) else [duty.team_id]
            team_member_ids: set[int] = set()
            for t_id in t_ids:
                team = self.team_repo.get_by_id(t_id)
                if team and team.member_ids:
                    team_member_ids.update(team.member_ids)
                elif team and team.members:
                    team_member_ids.update(m.user_id for m in team.members if m.user_id)

            # Trường hợp 1: Có liên kết với Meeting
            if duty.meeting_id:
                meeting = self.meeting_repo.get_by_id(duty.meeting_id)
                if meeting and meeting.participants:
                    candidates: list[int] = []
                    meeting_creator_id = getattr(meeting, "created_by", None)

                    for p in meeting.participants:
                        # 1. Bỏ qua nếu participant đã bị xóa
                        if getattr(p, "is_deleted", False):
                            continue

                        # 2. Bỏ qua nếu là người tạo/trainer của meeting
                        if meeting_creator_id and p.user_id == meeting_creator_id:
                            continue

                        # 3. Bỏ qua các trạng thái vắng mặt
                        if p.status in (
                            ParticipantStatus.ABSENT_EXCUSED,
                            ParticipantStatus.ABSENT_UNEXCUSED,
                        ):
                            continue

                        # 4. Phải có check_in_at thực tế (bao gồm cả học viên chính thức và học viên nhóm khác đổi lớp/học bù có mặt tại phòng Lab)
                        if p.check_in_at is not None:
                            candidates.append(p.user_id)

                    # Loại bỏ trùng lặp user_id
                    penalized_user_ids = list(dict.fromkeys(candidates))

                if not penalized_user_ids:
                    # Buổi học không có ai trong nhóm trực check-in / hủy lớp -> Hủy ca trực, không phạt oan
                    duty.status = DutyStatus.CANCELLED
                    self.duty_repo.save(duty)
                    logger.info(
                        f"Ca trực {duty.id} (nhóm {duty.team_id}) không có thành viên check-in -> Chuyển CANCELLED"
                    )
                    continue

                reason = f"Có mặt tại buổi học nhưng không hoàn thành trực nhật phòng Lab ngày {date_str}"

            # Trường hợp 2: Ca trực độc lập không có meeting
            else:
                if team_member_ids:
                    penalized_user_ids = list(team_member_ids)

                if not penalized_user_ids:
                    # Nhóm không có thành viên -> Hủy ca trực
                    duty.status = DutyStatus.CANCELLED
                    self.duty_repo.save(duty)
                    logger.info(
                        f"Ca trực tự do {duty.id} (nhóm {duty.team_id}) không có thành viên -> Chuyển CANCELLED"
                    )
                    continue

                reason = f"Không hoàn thành trực nhật phòng Lab ngày {date_str}"

            if penalized_user_ids:
                logger.warning(
                    f"Tạo vi phạm cho {len(penalized_user_ids)} học viên vì không trực nhật ca {duty.id}"
                )
                now_dt = get_current_utc7_time()
                await self.create_violation_use_case.execute(
                    user_ids=penalized_user_ids,
                    reason=reason,
                    date=now_dt,
                    is_system=True,
                )
                violations_count += len(penalized_user_ids)

                duty.status = DutyStatus.VIOLATED
                self.duty_repo.save(duty)

                await self.event_bus.publish(
                    cast(
                        DomainEvent,
                        DutyViolated(
                            duty_id=duty.id,
                            team_id=duty.team_id,
                            duty_date=str(duty.duty_date),
                            penalized_user_ids=penalized_user_ids,
                        ),
                    )
                )

        return violations_count
