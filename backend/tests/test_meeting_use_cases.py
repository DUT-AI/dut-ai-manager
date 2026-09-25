import asyncio
from datetime import datetime, date
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.meeting.application import CheckMeetingAttendanceUseCase
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import (
    ParticipantAbsenceRecorded,
    ParticipantLateRecorded,
)
from app.meeting.domain.value_objects import ParticipantStatus
import app.user.infrastructure.model  # noqa: F401
import app.homework.infrastructure.model  # noqa: F401
import app.permission_request.infrastructure.model  # noqa: F401
import app.violation.infrastructure.model  # noqa: F401


def test_check_meeting_attendance_decoupled_job():
    meeting_repo = MagicMock()
    participant_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    start_time = datetime(2026, 9, 10, 18, 0)
    end_time = datetime(2026, 9, 10, 21, 0)

    # Participant 1: Chưa check-in -> Phát ParticipantAbsenceRecorded
    p_no_checkin = MeetingParticipant(id=1, user_id=101, status=ParticipantStatus.NOT_JOINED)

    # Participant 2: Check-in đúng giờ, quên check-out -> Auto check_out_at = end_time, COMPLETED (Không phát event vi phạm)
    p_ontime = MeetingParticipant(
        id=2, user_id=102, check_in_at=datetime(2026, 9, 10, 18, 2), status=ParticipantStatus.JOINED
    )

    # Participant 3: Check-in trễ -> Phát ParticipantLateRecorded
    p_late = MeetingParticipant(
        id=3, user_id=103, check_in_at=datetime(2026, 9, 10, 18, 20), status=ParticipantStatus.JOINED
    )

    dummy_meeting = Meeting(
        id=10,
        title="Sinh hoạt định kỳ 10/9",
        start_time=start_time,
        end_time=end_time,
        require_check_in=True,
        participants=[
            p_no_checkin,
            p_ontime,
            p_late,
        ],
    )

    meeting_repo.get_by_date.return_value = [dummy_meeting]

    use_case = CheckMeetingAttendanceUseCase(
        meeting_repo=meeting_repo,
        participant_repo=participant_repo,
        event_bus=event_bus,
    )

    events_count = asyncio.run(use_case.execute(target_date=date(2026, 9, 10)))

    # Expect 2 events published (1 absence, 1 late)
    assert events_count == 2
    assert event_bus.publish.call_count == 2

    published_events = [call[0][0] for call in event_bus.publish.call_args_list]
    absence_events = [e for e in published_events if isinstance(e, ParticipantAbsenceRecorded)]
    late_events = [e for e in published_events if isinstance(e, ParticipantLateRecorded)]

    assert len(absence_events) == 1
    assert absence_events[0].user_id == 101
    assert absence_events[0].meeting_id == 10

    assert len(late_events) == 1
    assert late_events[0].user_id == 103
    assert late_events[0].meeting_id == 10

    # Assert participant auto checkout for on-time attendee
    assert p_ontime.status == ParticipantStatus.COMPLETED
    assert p_ontime.check_out_at == end_time

    print("CheckMeetingAttendanceUseCase decoupled tests PASSED!")


def test_meeting_repository_save_hard_deletes_removed_participants():
    """Kiểm tra MeetingRepository.save thực hiện session.delete đối với participant bị loại bỏ."""
    from app.meeting.infrastructure.repository import MeetingRepository
    from app.meeting.infrastructure.model import Meeting as ORMMeeting, MeetingParticipant as ORMParticipant

    session = MagicMock()

    orm_p1 = ORMParticipant(id=1, meeting_id=10, user_id=101)
    orm_p2 = ORMParticipant(id=2, meeting_id=10, user_id=102)

    orm_meeting = ORMMeeting(
        id=10,
        title="Test Meeting",
        start_time=datetime(2026, 9, 10, 18, 0),
        end_time=datetime(2026, 9, 10, 20, 0),
    )
    orm_meeting.participants = [orm_p1, orm_p2]

    session.get.return_value = orm_meeting
    session.scalars.return_value.all.return_value = [orm_p1, orm_p2]

    repo = MeetingRepository(session=session)

    # Cập nhật danh sách participant: chỉ giữ user 101, loại user 102, thêm user 103
    domain_meeting = Meeting(
        id=10,
        title="Test Meeting",
        start_time=datetime(2026, 9, 10, 18, 0),
        end_time=datetime(2026, 9, 10, 20, 0),
        participants=[
            MeetingParticipant(id=1, meeting_id=10, user_id=101),
            MeetingParticipant(user_id=103),
        ],
    )

    repo.save(domain_meeting)

    # Xác nhận session.delete được gọi cho orm_p2 (user 102 bị loại bỏ)
    session.delete.assert_called_once_with(orm_p2)
    session.flush.assert_called()
    session.refresh.assert_called_with(orm_meeting)


def test_meeting_mapping_filters_is_deleted_participants():
    """Kiểm tra Meeting.to_entity() và MeetingRepository._to_domain() bỏ qua participant is_deleted=True."""
    from app.meeting.infrastructure.repository import MeetingRepository
    from app.meeting.infrastructure.model import Meeting as ORMMeeting, MeetingParticipant as ORMParticipant

    orm_p_active = ORMParticipant(id=1, meeting_id=10, user_id=101)
    orm_p_active.is_deleted = False

    orm_p_deleted = ORMParticipant(id=2, meeting_id=10, user_id=102)
    orm_p_deleted.is_deleted = True

    orm_meeting = ORMMeeting(
        id=10,
        title="Test Meeting",
        start_time=datetime(2026, 9, 10, 18, 0),
        end_time=datetime(2026, 9, 10, 20, 0),
    )
    orm_meeting.participants = [orm_p_active, orm_p_deleted]

    # 1. Test model.to_entity()
    entity = orm_meeting.to_entity()
    assert len(entity.participants) == 1
    assert entity.participants[0].user_id == 101

    # 2. Test repo._to_domain()
    session = MagicMock()
    repo = MeetingRepository(session=session)
    domain = repo._to_domain(orm_meeting)
    assert len(domain.participants) == 1
    assert domain.participants[0].user_id == 101


if __name__ == "__main__":
    test_check_meeting_attendance_decoupled_job()
    test_meeting_repository_save_hard_deletes_removed_participants()
    test_meeting_mapping_filters_is_deleted_participants()
    print("All Meeting tests PASSED!")
