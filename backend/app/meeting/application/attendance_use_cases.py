"""
Meeting Attendance & Status Use Cases — application layer.

Handles 23:59 daily job meeting attendance checking, violation creation,
and manual participant status updates.
"""

from datetime import date, datetime

from fastapi import status

from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.application.response import BadRequestException
from app.utils.datetime import get_current_utc7_time
from app.violation.application.use_cases import CreateViolationUseCase


class CheckMeetingAttendanceUseCase:
    """Kiểm tra điểm danh các buổi họp & tạo vi phạm tự động lúc 23:59 hàng ngày"""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
        permission_repo: PermissionRequestRepository,
        create_violation_use_case: CreateViolationUseCase,
    ):
        self.meeting_repo = meeting_repo
        self.participant_repo = participant_repo
        self.permission_repo = permission_repo
        self.create_violation_use_case = create_violation_use_case

    async def execute(self, target_date: date | None = None) -> int:
        if target_date is None:
            now = get_current_utc7_time()
            target_date = now.date()

        meetings = self.meeting_repo.get_by_date(target_date)
        if not meetings:
            return 0

        active_meetings = [m for m in meetings if m.require_check_in]
        if not active_meetings:
            return 0

        meeting_ids = [m.id for m in active_meetings if m.id is not None]
        all_user_ids = list(
            {p.user_id for m in active_meetings for p in m.participants}
        )

        if not all_user_ids:
            return 0

        requests = self.permission_repo.get_requests_for_meetings(
            meeting_ids, all_user_ids
        )

        absence_set: set[tuple[int, int | None]] = set()
        late_request_map: dict[tuple[int, int | None], PermissionRequest] = {}

        for req in requests:
            if req.category == RequestCategory.ABSENCE:
                if req.meeting_id:
                    absence_set.add((req.user_id, req.meeting_id))
                else:
                    absence_set.add((req.user_id, None))
            elif req.category == RequestCategory.LATE:
                if req.meeting_id:
                    late_request_map[(req.user_id, req.meeting_id)] = req
                else:
                    late_request_map[(req.user_id, None)] = req

        created_violations_count = 0
        now_utc7 = get_current_utc7_time()
        violation_date = (
            datetime.combine(target_date, datetime.min.time())
            if target_date != now_utc7.date()
            else now_utc7
        )

        for meeting in active_meetings:
            m_id = meeting.id or 0
            for participant in meeting.participants:
                user_id = participant.user_id

                has_absence_perm = (user_id, m_id) in absence_set or (
                    user_id,
                    None,
                ) in absence_set
                late_perm = late_request_map.get(
                    (user_id, m_id)
                ) or late_request_map.get((user_id, None))

                # Trường hợp A: Không check-in
                if participant.check_in_at is None:
                    if has_absence_perm:
                        participant.status = ParticipantStatus.ABSENT_EXCUSED
                        self.participant_repo.save(participant)
                    else:
                        participant.status = ParticipantStatus.ABSENT_UNEXCUSED
                        self.participant_repo.save(participant)

                        reason = f"Vắng sinh hoạt: {meeting.title} (Không xin phép)"
                        violations = await self.create_violation_use_case.execute(
                            user_ids=[user_id],
                            reason=reason,
                            date=violation_date,
                            is_system=True,
                        )
                        if violations:
                            created_violations_count += len(violations)

                # Trường hợp B: Đã check-in
                else:
                    if participant.check_out_at is None:
                        participant.check_out_at = meeting.end_time

                    is_late = meeting.is_late(participant.check_in_at)
                    if not is_late:
                        participant.status = ParticipantStatus.COMPLETED
                        self.participant_repo.save(participant)
                    else:
                        if late_perm is None:
                            participant.status = ParticipantStatus.LATE_UNEXCUSED
                            self.participant_repo.save(participant)

                            reason = f"Đi trễ sinh hoạt: {meeting.title} (Không xin phép)"
                            violations = await self.create_violation_use_case.execute(
                                user_ids=[user_id],
                                reason=reason,
                                date=violation_date,
                                is_system=True,
                            )
                            if violations:
                                created_violations_count += len(violations)
                        else:
                            if (
                                late_perm.start_time
                                and participant.check_in_at <= late_perm.start_time
                            ):
                                participant.status = ParticipantStatus.LATE_EXCUSED
                                self.participant_repo.save(participant)
                            else:
                                participant.status = ParticipantStatus.LATE_UNEXCUSED
                                self.participant_repo.save(participant)

                                limit_str = (
                                    late_perm.start_time.strftime("%H:%M")
                                    if late_perm.start_time
                                    else "thời gian quy định"
                                )
                                reason = f"Đi trễ hơn thời gian xin phép ({limit_str}): {meeting.title}"
                                violations = await self.create_violation_use_case.execute(
                                    user_ids=[user_id],
                                    reason=reason,
                                    date=violation_date,
                                    is_system=True,
                                )
                                if violations:
                                    created_violations_count += len(violations)

        return created_violations_count


class UpdateParticipantStatusUseCase:
    """Cập nhật thủ công trạng thái của thành viên trong meeting (người tạo meeting / Admin)"""

    def __init__(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
    ):
        self.meeting_repo = meeting_repo
        self.participant_repo = participant_repo

    def execute(
        self,
        meeting_id: int,
        user_id: int,
        target_status: ParticipantStatus,
        check_in_at: datetime | None = None,
        check_out_at: datetime | None = None,
    ) -> MeetingParticipant:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise BadRequestException(
                "Không tìm thấy buổi họp", status_code=status.HTTP_404_NOT_FOUND
            )

        if check_in_at is None and target_status in (
            ParticipantStatus.JOINED,
            ParticipantStatus.LATE_EXCUSED,
            ParticipantStatus.LATE_UNEXCUSED,
            ParticipantStatus.COMPLETED,
        ):
            check_in_at = meeting.start_time

        if check_out_at is None and target_status == ParticipantStatus.COMPLETED:
            check_out_at = meeting.end_time

        updated = self.participant_repo.update_participant_status(
            meeting_id=meeting_id,
            user_id=user_id,
            status=target_status,
            check_in_at=check_in_at,
            check_out_at=check_out_at,
        )
        return updated
