from datetime import UTC, datetime

from app.meeting.domain.entity import MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus


def test_record_check_in_on_time():
    """Check-in đúng giờ: status thành JOINED, ghi nhận check_in_at, link_image và client_event_id."""
    meeting_start = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
    check_in_time = datetime(2026, 10, 30, 11, 55, tzinfo=UTC)

    participant = MeetingParticipant(
        id=1,
        meeting_id=10,
        user_id=101,
        status=ParticipantStatus.NOT_JOINED,
    )

    success, message, is_late = participant.record_check_in(
        check_in_time=check_in_time,
        meeting_start_time=meeting_start,
        image_url="https://minio/checkin1.jpg",
        client_event_id="evt_bulk_1",
    )

    assert success is True
    assert is_late is False
    assert participant.status == ParticipantStatus.JOINED
    assert participant.check_in_at == check_in_time
    assert participant.link_image == "https://minio/checkin1.jpg"
    assert participant.client_event_id == "evt_bulk_1"


def test_record_check_in_late_unexcused():
    """Check-in trễ không phép: status thành LATE_UNEXCUSED, is_late là True."""
    meeting_start = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
    check_in_time = datetime(2026, 10, 30, 12, 15, tzinfo=UTC)

    participant = MeetingParticipant(
        id=2,
        meeting_id=10,
        user_id=102,
        status=ParticipantStatus.NOT_JOINED,
    )

    success, message, is_late = participant.record_check_in(
        check_in_time=check_in_time,
        meeting_start_time=meeting_start,
        image_url="https://minio/checkin_late.jpg",
    )

    assert success is True
    assert is_late is True
    assert participant.status == ParticipantStatus.LATE_UNEXCUSED
    assert participant.check_in_at == check_in_time
    assert participant.link_image == "https://minio/checkin_late.jpg"


def test_record_check_in_preserves_late_excused():
    """Học viên có đơn xin đi trễ (LATE_EXCUSED): luôn ghi nhận check_in_at và ảnh nhưng BẢO LƯU LATE_EXCUSED."""
    meeting_start = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
    check_in_time = datetime(2026, 10, 30, 12, 25, tzinfo=UTC)

    participant = MeetingParticipant(
        id=3,
        meeting_id=10,
        user_id=103,
        status=ParticipantStatus.LATE_EXCUSED,
        check_in_at=None,
    )

    success, message, is_late = participant.record_check_in(
        check_in_time=check_in_time,
        meeting_start_time=meeting_start,
        image_url="https://minio/excused.jpg",
    )

    assert success is True
    assert is_late is True
    assert participant.status == ParticipantStatus.LATE_EXCUSED
    assert participant.check_in_at == check_in_time
    assert participant.link_image == "https://minio/excused.jpg"


def test_record_check_in_rejected_when_completed():
    """Học viên đã hoàn thành (COMPLETED): từ chối ghi nhận điểm danh đè."""
    meeting_start = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
    check_in_time = datetime(2026, 10, 30, 12, 5, tzinfo=UTC)
    original_check_in = datetime(2026, 10, 30, 11, 58, tzinfo=UTC)

    participant = MeetingParticipant(
        id=4,
        meeting_id=10,
        user_id=104,
        status=ParticipantStatus.COMPLETED,
        check_in_at=original_check_in,
        link_image="https://minio/old.jpg",
    )

    success, message, is_late = participant.record_check_in(
        check_in_time=check_in_time,
        meeting_start_time=meeting_start,
        image_url="https://minio/new.jpg",
    )

    assert success is False
    assert participant.status == ParticipantStatus.COMPLETED
    assert participant.check_in_at == original_check_in
    assert participant.link_image == "https://minio/old.jpg"


def test_record_check_in_updates_image_when_already_joined():
    """Học viên đã JOINED (ví dụ điểm danh nhanh trên web chưa có ảnh) -> cho phép cập nhật ảnh mới."""
    meeting_start = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
    original_check_in = datetime(2026, 10, 30, 11, 55, tzinfo=UTC)
    new_check_in = datetime(2026, 10, 30, 12, 2, tzinfo=UTC)

    participant = MeetingParticipant(
        id=5,
        meeting_id=10,
        user_id=105,
        status=ParticipantStatus.JOINED,
        check_in_at=original_check_in,
        link_image=None,
    )

    success, message, is_late = participant.record_check_in(
        check_in_time=new_check_in,
        meeting_start_time=meeting_start,
        image_url="https://minio/new_face.jpg",
    )

    assert success is True
    assert participant.status == ParticipantStatus.JOINED
    # check_in_at giữ mốc ban đầu (hoặc nếu là None thì được gán)
    assert participant.check_in_at == original_check_in
    assert participant.link_image == "https://minio/new_face.jpg"
