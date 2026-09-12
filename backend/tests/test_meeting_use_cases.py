import asyncio
from datetime import datetime, date
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Thêm thư mục backend vào sys.path để chạy trực tiếp không bị lỗi ModuleNotFoundError: No module named 'app'
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.meeting.application.use_cases import CheckMeetingAttendanceUseCase
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus


def test_check_meeting_attendance_completed_status():
    """Verify that participants with COMPLETED status (checked out) are not flagged as absent."""
    meeting_repo = MagicMock()
    permission_repo = MagicMock()
    permission_repo.get_user_ids_with_requests_for_date.return_value = set()

    p_not_joined = MeetingParticipant(
        id=1, user_id=101, status=ParticipantStatus.NOT_JOINED
    )
    p_joined = MeetingParticipant(
        id=2, user_id=102, status=ParticipantStatus.JOINED
    )
    p_completed = MeetingParticipant(
        id=3, user_id=103, status=ParticipantStatus.COMPLETED
    )

    dummy_meeting = Meeting(
        id=10,
        title="Sinh hoạt định kỳ 10/9",
        start_time=datetime(2026, 9, 10, 18, 0),
        end_time=datetime(2026, 9, 10, 21, 0),
        require_check_in=True,
        participants=[p_not_joined, p_joined, p_completed],
    )

    meeting_repo.get_by_date.return_value = [dummy_meeting]

    use_case = CheckMeetingAttendanceUseCase(
        meeting_repo=meeting_repo,
        permission_repo=permission_repo,
    )

    with patch("app.shared.domain.event_bus.EventBus.publish", new_callable=AsyncMock) as mock_publish:
        created_count = asyncio.run(use_case.execute(target_date=date(2026, 9, 10)))

        # Only p_not_joined (user_id=101) should generate a MeetingAbsenceDetected event
        assert created_count == 1
        assert mock_publish.call_count == 1

        event_arg = mock_publish.call_args[0][0]
        assert event_arg.user_id == 101


if __name__ == "__main__":
    test_check_meeting_attendance_completed_status()
    print("All meeting use case tests passed!")
