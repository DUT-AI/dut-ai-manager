import asyncio
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import app.homework.infrastructure.model  # noqa: F401
import app.permission_request.infrastructure.model  # noqa: F401
import app.user.infrastructure.model  # noqa: F401
import app.violation.infrastructure.model  # noqa: F401
from app.meeting.application import CheckMeetingAttendanceUseCase
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.events import (
    ParticipantAbsenceRecorded,
    ParticipantLateRecorded,
)
from app.meeting.domain.value_objects import ParticipantStatus


def test_check_meeting_attendance_decoupled_job():
    meeting_repo = MagicMock()
    participant_repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    start_time = datetime(2026, 9, 10, 18, 0)
    end_time = datetime(2026, 9, 10, 21, 0)

    # Participant 1: Chưa check-in -> Phát ParticipantAbsenceRecorded
    p_no_checkin = MeetingParticipant(
        id=1, user_id=101, status=ParticipantStatus.NOT_JOINED
    )

    # Participant 2: Check-in đúng giờ, quên check-out -> Auto check_out_at = end_time, COMPLETED (Không phát event vi phạm)
    p_ontime = MeetingParticipant(
        id=2,
        user_id=102,
        check_in_at=datetime(2026, 9, 10, 18, 2),
        status=ParticipantStatus.JOINED,
    )

    # Participant 3: Check-in trễ -> Phát ParticipantLateRecorded
    p_late = MeetingParticipant(
        id=3,
        user_id=103,
        check_in_at=datetime(2026, 9, 10, 18, 20),
        status=ParticipantStatus.JOINED,
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
    absence_events = [
        e for e in published_events if isinstance(e, ParticipantAbsenceRecorded)
    ]
    late_events = [
        e for e in published_events if isinstance(e, ParticipantLateRecorded)
    ]

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
    from app.meeting.infrastructure.model import (
        Meeting as ORMMeeting,
    )
    from app.meeting.infrastructure.model import (
        MeetingParticipant as ORMParticipant,
    )
    from app.meeting.infrastructure.repository import MeetingRepository

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
    from app.meeting.infrastructure.model import (
        Meeting as ORMMeeting,
    )
    from app.meeting.infrastructure.model import (
        MeetingParticipant as ORMParticipant,
    )
    from app.meeting.infrastructure.repository import MeetingRepository

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


def test_update_meeting_preserves_participant_attendance_status():
    """Kiểm tra UpdateMeetingUseCase không reset trạng thái điểm danh của participant cũ khi cập nhật meeting."""
    from app.meeting.application.update_meeting_use_case import UpdateMeetingUseCase
    from app.meeting.schemas import MeetingUpdate

    repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    check_in_dt = datetime(2026, 9, 10, 18, 5)
    existing_p = MeetingParticipant(
        id=1,
        meeting_id=10,
        user_id=101,
        status=ParticipantStatus.JOINED,
        check_in_at=check_in_dt,
        link_image="https://example.com/face.jpg",
    )

    domain_meeting = Meeting(
        id=10,
        title="Old Title",
        start_time=datetime(2026, 9, 10, 18, 0),
        end_time=datetime(2026, 9, 10, 20, 0),
        participants=[existing_p],
    )

    repo.get_with_participants.return_value = domain_meeting
    # When repo.save is called, return the domain object passed to it
    repo.save.side_effect = lambda m: m

    use_case = UpdateMeetingUseCase(repo=repo, event_bus=event_bus)

    # Cập nhật danh sách user_ids gồm user 101 (cũ) và 102 (mới)
    update_data = MeetingUpdate(
        title="New Title",
        user_ids=[101, 102],
    )

    updated_meeting = asyncio.run(use_case.execute(meeting_id=10, data=update_data))

    repo.get_with_participants.assert_called_once_with(10)
    assert updated_meeting.title == "New Title"
    assert len(updated_meeting.participants) == 2

    # Tìm participant 101
    p101 = next(p for p in updated_meeting.participants if p.user_id == 101)
    assert p101.status == ParticipantStatus.JOINED
    assert p101.check_in_at == check_in_dt
    assert p101.link_image == "https://example.com/face.jpg"

    # Tìm participant 102 (mới)
    p102 = next(p for p in updated_meeting.participants if p.user_id == 102)
    assert p102.status == ParticipantStatus.NOT_JOINED
    assert p102.check_in_at is None


def test_update_meeting_without_user_ids_preserves_participants():
    """Kiểm tra UpdateMeetingUseCase không làm mất participants khi không truyền user_ids."""
    from app.meeting.application.update_meeting_use_case import UpdateMeetingUseCase
    from app.meeting.schemas import MeetingUpdate

    repo = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    existing_p = MeetingParticipant(
        id=1,
        meeting_id=10,
        user_id=101,
        status=ParticipantStatus.JOINED,
        check_in_at=datetime(2026, 9, 10, 18, 5),
    )

    domain_meeting = Meeting(
        id=10,
        title="Old Title",
        start_time=datetime(2026, 9, 10, 18, 0),
        end_time=datetime(2026, 9, 10, 20, 0),
        participants=[existing_p],
    )

    repo.get_with_participants.return_value = domain_meeting
    repo.save.side_effect = lambda m: m

    use_case = UpdateMeetingUseCase(repo=repo, event_bus=event_bus)

    # Chỉ cập nhật title, user_ids=None
    update_data = MeetingUpdate(title="Updated Title Only")
    updated_meeting = asyncio.run(use_case.execute(meeting_id=10, data=update_data))

    assert updated_meeting.title == "Updated Title Only"
    assert len(updated_meeting.participants) == 1
    assert updated_meeting.participants[0].user_id == 101
    assert updated_meeting.participants[0].status == ParticipantStatus.JOINED


def test_participant_repository_save_persists_all_fields():
    """Kiểm tra ParticipantRepository.save ánh xạ và lưu đầy đủ các trường bao gồm client_event_id."""
    from app.meeting.infrastructure.model import MeetingParticipant as ORMParticipant
    from app.meeting.infrastructure.repository import ParticipantRepository

    session = MagicMock()
    orm_p = ORMParticipant(id=1, meeting_id=10, user_id=101)
    session.get.return_value = orm_p

    repo = ParticipantRepository(session=session)

    check_in_dt = datetime(2026, 10, 30, 12, 10, tzinfo=UTC)
    domain_p = MeetingParticipant(
        id=1,
        meeting_id=10,
        user_id=101,
        status=ParticipantStatus.LATE_UNEXCUSED,
        check_in_at=check_in_dt,
        link_image="https://minio/proof.jpg",
        client_event_id="evt_test_123",
    )

    saved = repo.save(domain_p)

    assert saved.id == 1
    assert orm_p.status == ParticipantStatus.LATE_UNEXCUSED
    assert orm_p.check_in_at == check_in_dt
    assert orm_p.link_image == "https://minio/proof.jpg"
    assert orm_p.client_event_id == "evt_test_123"
    session.add.assert_called_once_with(orm_p)
    session.flush.assert_called_once()


def test_checkin_use_case_delegates_to_domain_and_preserves_late_excused():
    """Kiểm tra CheckInUseCase ủy quyền cho Domain Entity, bảo lưu LATE_EXCUSED và ghi nhận check_in_at."""
    from unittest.mock import AsyncMock, MagicMock

    from app.meeting.application.checkin_use_case import CheckInUseCase
    from app.meeting.domain.events import ParticipantCheckedIn

    meeting_repo = MagicMock()
    participant_repo = MagicMock()
    minio_service = MagicMock()
    minio_service.upload_file = AsyncMock(return_value="https://minio/bulk_face.jpg")
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    meeting_start = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
    meeting_end = datetime(2026, 10, 30, 14, 0, tzinfo=UTC)
    check_in_time = datetime(2026, 10, 30, 12, 20, tzinfo=UTC)

    dummy_meeting = Meeting(
        id=10,
        title="Buổi sinh hoạt DDD",
        start_time=meeting_start,
        end_time=meeting_end,
    )
    meeting_repo.get_domain_for_check_in.return_value = dummy_meeting

    participant = MeetingParticipant(
        id=1,
        meeting_id=10,
        user_id=101,
        status=ParticipantStatus.LATE_EXCUSED,
        check_in_at=None,
    )
    participant_repo.find_all_participations_in_time_window.return_value = [participant]
    participant_repo.save.side_effect = lambda p: p

    mock_image = MagicMock()
    mock_image.read = AsyncMock(return_value=b"fake-image-bytes")
    mock_image.filename = "cam.jpg"
    mock_image.content_type = "image/jpeg"

    uc = CheckInUseCase(
        meeting_repo=meeting_repo,
        participant_repo=participant_repo,
        minio_service=minio_service,
        event_bus=event_bus,
    )

    updated_participants, msg = asyncio.run(
        uc.execute(
            user_ids=[101],
            image=mock_image,
            client_time="2026-10-30T12:20:00Z",
            client_event_id="evt_bulk_99",
        )
    )

    assert len(updated_participants) == 1
    p = updated_participants[0]
    assert p.status == ParticipantStatus.LATE_EXCUSED
    assert p.check_in_at == check_in_time
    assert p.link_image == "https://minio/bulk_face.jpg"
    assert p.client_event_id == "evt_bulk_99"

    event_bus.publish.assert_called_once()
    published_event = event_bus.publish.call_args[0][0]
    assert isinstance(published_event, ParticipantCheckedIn)
    assert published_event.user_id == 101
    assert published_event.meeting_id == 10
    assert published_event.is_late is True
    assert published_event.check_in_at == check_in_time


def test_checkin_with_card_use_case_delegates_to_domain_and_preserves_late_excused():
    """Kiểm tra CheckInWithCardUseCase ủy quyền cho Domain Entity, bảo lưu LATE_EXCUSED và ghi nhận check_in_at."""
    from unittest.mock import AsyncMock, MagicMock

    from app.meeting.application.checkin_with_card_use_case import (
        CheckInWithCardUseCase,
    )
    from app.meeting.domain.events import ParticipantCheckedIn

    user_repo = MagicMock()
    meeting_repo = MagicMock()
    participant_repo = MagicMock()
    tts_service = MagicMock()
    tts_service.synthesize_with_cache = AsyncMock(return_value=b"RIFF_FAKE_AUDIO_BYTES")
    minio_service = MagicMock()
    minio_service.get_file = AsyncMock(return_value=None)
    minio_service.upload_file = AsyncMock(return_value="https://minio/tts.wav")
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()

    meeting_start = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
    meeting_end = datetime(2026, 10, 30, 14, 0, tzinfo=UTC)

    dummy_user = MagicMock()
    dummy_user.id = 101
    dummy_user.name = "Nguyen Van A"
    user_repo.get_summary_by_card_code.return_value = dummy_user

    dummy_meeting = Meeting(
        id=10,
        title="Buổi sinh hoạt Card",
        start_time=meeting_start,
        end_time=meeting_end,
    )
    meeting_repo.get_domain_for_check_in.return_value = dummy_meeting

    participant = MeetingParticipant(
        id=1,
        meeting_id=10,
        user_id=101,
        status=ParticipantStatus.LATE_EXCUSED,
        check_in_at=None,
    )
    participant_repo.find_participation_in_time_window.return_value = participant
    participant_repo.save.side_effect = lambda p: p

    uc = CheckInWithCardUseCase(
        user_repo=user_repo,
        meeting_repo=meeting_repo,
        participant_repo=participant_repo,
        tts_service=tts_service,
        minio_service=minio_service,
        event_bus=event_bus,
    )

    msg, audio = asyncio.run(uc.execute(card_code="CARD_123456"))

    assert "thành công" in msg
    assert audio == b"RIFF_FAKE_AUDIO_BYTES"
    assert participant.status == ParticipantStatus.LATE_EXCUSED
    assert participant.check_in_at is not None

    event_bus.publish.assert_called_once()
    published_event = event_bus.publish.call_args[0][0]
    assert isinstance(published_event, ParticipantCheckedIn)
    assert published_event.user_id == 101
    assert published_event.meeting_id == 10


def test_update_participant_status_option_a_business_rules():
    """Kiểm tra Phương án A:

    - Chọn JOINED mà để trống giờ -> Gán start_time
    - Chọn LATE_* mà để trống giờ (trong giờ học) -> Gán now
    - Nhập giờ tường minh -> Lấy đúng giờ người dùng nhập
    """
    from app.meeting.application.update_participant_status_use_case import (
        UpdateParticipantStatusUseCase,
    )

    meeting_repo = MagicMock()
    participant_repo = MagicMock()

    meeting_start = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)  # 19:00 VN
    meeting_end = datetime(2026, 11, 1, 14, 0, tzinfo=UTC)  # 21:00 VN

    dummy_meeting = Meeting(
        id=833,
        title="Test Meeting Option A",
        start_time=meeting_start,
        end_time=meeting_end,
    )
    meeting_repo.get_by_id.return_value = dummy_meeting

    # 1. Trường hợp JOINED (Đúng giờ) và để trống giờ check-in -> Phải nhận meeting_start (19:00 VN)
    participant_1 = MeetingParticipant(
        id=1,
        meeting_id=833,
        user_id=10,
        status=ParticipantStatus.NOT_JOINED,
        check_in_at=None,
    )
    participant_repo.get_by_meeting_and_user.return_value = participant_1
    participant_repo.update_participant_status.side_effect = (
        lambda meeting_id, user_id, status, check_in_at, check_out_at: (
            MeetingParticipant(
                id=1,
                meeting_id=meeting_id,
                user_id=user_id,
                status=status,
                check_in_at=check_in_at,
                check_out_at=check_out_at,
            )
        )
    )

    uc = UpdateParticipantStatusUseCase(
        meeting_repo=meeting_repo,
        participant_repo=participant_repo,
    )

    # Chọn JOINED, để trống check_in_at
    res_1 = uc.execute(
        meeting_id=833,
        user_id=10,
        target_status=ParticipantStatus.JOINED,
        check_in_at=None,
    )
    assert res_1.status == ParticipantStatus.JOINED
    assert res_1.check_in_at == meeting_start  # Luôn là 12:00 UTC (19:00 VN)

    # 2. Trường hợp nhập giờ tường minh -> Phải lấy đúng giờ nhập
    explicit_time = datetime(2026, 11, 1, 12, 15, tzinfo=UTC)
    res_2 = uc.execute(
        meeting_id=833,
        user_id=10,
        target_status=ParticipantStatus.JOINED,
        check_in_at=explicit_time,
    )
    assert res_2.check_in_at == explicit_time


if __name__ == "__main__":
    test_check_meeting_attendance_decoupled_job()
    test_meeting_repository_save_hard_deletes_removed_participants()
    test_meeting_mapping_filters_is_deleted_participants()
    test_update_meeting_preserves_participant_attendance_status()
    test_update_meeting_without_user_ids_preserves_participants()
    print("All Meeting tests PASSED!")
