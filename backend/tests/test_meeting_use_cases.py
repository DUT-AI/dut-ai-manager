import asyncio
from datetime import datetime, date
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.meeting.application.use_cases import CheckMeetingAttendanceUseCase
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus
from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.value_objects import RequestCategory


def test_check_meeting_attendance_refactored_job():
    meeting_repo = MagicMock()
    participant_repo = MagicMock()
    permission_repo = MagicMock()
    create_violation_uc = MagicMock()
    create_violation_uc.execute = AsyncMock(return_value=[MagicMock()])

    start_time = datetime(2026, 9, 10, 18, 0)
    end_time = datetime(2026, 9, 10, 21, 0)

    # Participant 1: Chưa check-in, KHÔNG xin phép vắng -> ABSENT_UNEXCUSED & Vi phạm
    p_no_checkin = MeetingParticipant(id=1, user_id=101, status=ParticipantStatus.NOT_JOINED)

    # Participant 2: Chưa check-in, CÓ xin phép vắng -> ABSENT_EXCUSED (Không vi phạm)
    p_absent_excused = MeetingParticipant(id=2, user_id=102, status=ParticipantStatus.NOT_JOINED)

    # Participant 3: Check-in đúng giờ, quên check-out -> Auto check_out_at = end_time, COMPLETED (Không vi phạm)
    p_ontime = MeetingParticipant(
        id=3, user_id=103, check_in_at=datetime(2026, 9, 10, 18, 2), status=ParticipantStatus.JOINED
    )

    # Participant 4: Check-in trễ, KHÔNG xin phép -> LATE_UNEXCUSED & Vi phạm
    p_late_unexcused = MeetingParticipant(
        id=4, user_id=104, check_in_at=datetime(2026, 9, 10, 18, 20), status=ParticipantStatus.JOINED
    )

    # Participant 5: Check-in trễ, CÓ xin phép (hẹn 18:30), check-in 18:25 -> LATE_EXCUSED (Không vi phạm)
    p_late_excused = MeetingParticipant(
        id=5, user_id=105, check_in_at=datetime(2026, 9, 10, 18, 25), status=ParticipantStatus.JOINED
    )

    # Participant 6: Check-in trễ, CÓ xin phép (hẹn 18:15), check-in 18:30 -> LATE_UNEXCUSED & Vi phạm
    p_late_over_permission = MeetingParticipant(
        id=6, user_id=106, check_in_at=datetime(2026, 9, 10, 18, 30), status=ParticipantStatus.JOINED
    )

    dummy_meeting = Meeting(
        id=10,
        title="Sinh hoạt định kỳ 10/9",
        start_time=start_time,
        end_time=end_time,
        require_check_in=True,
        participants=[
            p_no_checkin,
            p_absent_excused,
            p_ontime,
            p_late_unexcused,
            p_late_excused,
            p_late_over_permission,
        ],
    )

    meeting_repo.get_by_date.return_value = [dummy_meeting]

    # Requests
    req_absent = PermissionRequest(
        id=1, user_id=102, category=RequestCategory.ABSENCE, note="Bận thi", meeting_id=10
    )
    req_late_ok = PermissionRequest(
        id=2, user_id=105, category=RequestCategory.LATE, note="Kẹt xe", meeting_id=10, start_time=datetime(2026, 9, 10, 18, 30)
    )
    req_late_over = PermissionRequest(
        id=3, user_id=106, category=RequestCategory.LATE, note="Xin đi trễ", meeting_id=10, start_time=datetime(2026, 9, 10, 18, 15)
    )

    permission_repo.get_requests_for_meetings.return_value = [req_absent, req_late_ok, req_late_over]

    use_case = CheckMeetingAttendanceUseCase(
        meeting_repo=meeting_repo,
        participant_repo=participant_repo,
        permission_repo=permission_repo,
        create_violation_use_case=create_violation_uc,
    )

    violation_count = asyncio.run(use_case.execute(target_date=date(2026, 9, 10)))

    # Expect 3 violations created (p_no_checkin, p_late_unexcused, p_late_over_permission)
    assert violation_count == 3
    assert create_violation_uc.execute.call_count == 3

    # Assert participant statuses & auto checkout
    assert p_no_checkin.status == ParticipantStatus.ABSENT_UNEXCUSED
    assert p_absent_excused.status == ParticipantStatus.ABSENT_EXCUSED

    assert p_ontime.status == ParticipantStatus.COMPLETED
    assert p_ontime.check_out_at == end_time

    assert p_late_unexcused.status == ParticipantStatus.LATE_UNEXCUSED
    assert p_late_unexcused.check_out_at == end_time

    assert p_late_excused.status == ParticipantStatus.LATE_EXCUSED
    assert p_late_excused.check_out_at == end_time

    assert p_late_over_permission.status == ParticipantStatus.LATE_UNEXCUSED
    assert p_late_over_permission.check_out_at == end_time

    print("CheckMeetingAttendanceUseCase refactored tests PASSED!")


if __name__ == "__main__":
    test_check_meeting_attendance_refactored_job()
