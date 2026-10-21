"""
Unit tests for UpcomingMeetingTaskScanner.
Tests candidate scanning, 48h lookahead window, stage calculation,
and participant status filtering (JOINED, COMPLETED, ABSENT_EXCUSED, deleted).
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.value_objects import ParticipantStatus
from app.reminder.application.scanners.upcoming_meeting_scanner import (
    UpcomingMeetingTaskScanner,
)
from app.reminder.domain.entity import ReminderStage, TaskType


@pytest.fixture
def mock_meeting_repo():
    return MagicMock()


def test_upcoming_meeting_scanner_finds_candidate_for_offset_1h(mock_meeting_repo):
    """Buổi họp bắt đầu sau 1 giờ (OFFSET_1H) phải sinh ứng viên nhắc nhở cho thành viên NOT_JOINED."""
    now = datetime(2026, 10, 21, 14, 0, 0)
    start_time = now + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    participant = MeetingParticipant(
        id=1,
        user_id=101,
        meeting_id=10,
        status=ParticipantStatus.NOT_JOINED,
        is_deleted=False,
    )
    meeting = Meeting(
        id=10,
        title="Họp Ban Công Nghệ",
        start_time=start_time,
        end_time=end_time,
        participants=[participant],
    )

    mock_meeting_repo.get_all_with_participants.return_value = [meeting]

    scanner = UpcomingMeetingTaskScanner(meeting_repo=mock_meeting_repo)
    candidates = scanner.scan_pending_tasks(now=now)

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.task_type == TaskType.MEETING
    assert candidate.task_id == 10
    assert candidate.user_id == 101
    assert candidate.task_title == "Cuộc họp: Họp Ban Công Nghệ"
    assert candidate.deadline == start_time
    assert candidate.action_url == "/dashboard/meetings/10"
    assert ReminderStage.OFFSET_1H in candidate.stages


def test_upcoming_meeting_scanner_ignores_already_checked_in_participants(
    mock_meeting_repo,
):
    """Thành viên đã điểm danh (JOINED hoặc COMPLETED) hoặc bị xóa mềm không được nhắc nhở."""
    now = datetime(2026, 10, 21, 14, 0, 0)
    start_time = now + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    p_joined = MeetingParticipant(
        id=1,
        user_id=101,
        meeting_id=10,
        status=ParticipantStatus.JOINED,
        is_deleted=False,
    )
    p_completed = MeetingParticipant(
        id=2,
        user_id=102,
        meeting_id=10,
        status=ParticipantStatus.COMPLETED,
        is_deleted=False,
    )
    p_deleted = MeetingParticipant(
        id=3,
        user_id=103,
        meeting_id=10,
        status=ParticipantStatus.NOT_JOINED,
        is_deleted=True,
    )

    meeting = Meeting(
        id=10,
        title="Họp Ban Công Nghệ",
        start_time=start_time,
        end_time=end_time,
        participants=[p_joined, p_completed, p_deleted],
    )

    mock_meeting_repo.get_all_with_participants.return_value = [meeting]

    scanner = UpcomingMeetingTaskScanner(meeting_repo=mock_meeting_repo)
    candidates = scanner.scan_pending_tasks(now=now)

    assert len(candidates) == 0


def test_upcoming_meeting_scanner_ignores_excused_absence(mock_meeting_repo):
    """Thành viên có đơn xin vắng được duyệt (ABSENT_EXCUSED) phải được tự động loại trừ."""
    now = datetime(2026, 10, 21, 14, 0, 0)
    start_time = now + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    p_absent_excused = MeetingParticipant(
        id=1,
        user_id=101,
        meeting_id=10,
        status=ParticipantStatus.ABSENT_EXCUSED,
        is_deleted=False,
    )
    p_not_joined = MeetingParticipant(
        id=2,
        user_id=102,
        meeting_id=10,
        status=ParticipantStatus.NOT_JOINED,
        is_deleted=False,
    )

    meeting = Meeting(
        id=10,
        title="Họp Ban Công Nghệ",
        start_time=start_time,
        end_time=end_time,
        participants=[p_absent_excused, p_not_joined],
    )

    mock_meeting_repo.get_all_with_participants.return_value = [meeting]

    scanner = UpcomingMeetingTaskScanner(meeting_repo=mock_meeting_repo)
    candidates = scanner.scan_pending_tasks(now=now)

    assert len(candidates) == 1
    assert candidates[0].user_id == 102


def test_upcoming_meeting_scanner_ignores_finished_meeting(mock_meeting_repo):
    """Buổi họp đã kết thúc không được quét nhắc nhở tham gia."""
    now = datetime(2026, 10, 21, 18, 0, 0)
    start_time = datetime(2026, 10, 21, 14, 0, 0)
    end_time = datetime(2026, 10, 21, 16, 0, 0)

    p = MeetingParticipant(
        id=1,
        user_id=101,
        meeting_id=10,
        status=ParticipantStatus.NOT_JOINED,
        is_deleted=False,
    )
    meeting = Meeting(
        id=10,
        title="Họp Đã Qua",
        start_time=start_time,
        end_time=end_time,
        participants=[p],
    )

    mock_meeting_repo.get_all_with_participants.return_value = [meeting]

    scanner = UpcomingMeetingTaskScanner(meeting_repo=mock_meeting_repo)
    candidates = scanner.scan_pending_tasks(now=now)

    assert len(candidates) == 0


def test_upcoming_meeting_scanner_no_matching_stage(mock_meeting_repo):
    """Buổi họp bắt đầu sau 10 giờ (không rơi vào mốc stage nào) không sinh ứng viên."""
    now = datetime(2026, 10, 21, 14, 0, 0)
    start_time = now + timedelta(hours=10)
    end_time = start_time + timedelta(hours=2)

    p = MeetingParticipant(
        id=1,
        user_id=101,
        meeting_id=10,
        status=ParticipantStatus.NOT_JOINED,
        is_deleted=False,
    )
    meeting = Meeting(
        id=10,
        title="Họp Tương Lai",
        start_time=start_time,
        end_time=end_time,
        participants=[p],
    )

    mock_meeting_repo.get_all_with_participants.return_value = [meeting]

    scanner = UpcomingMeetingTaskScanner(meeting_repo=mock_meeting_repo)
    candidates = scanner.scan_pending_tasks(now=now)

    assert len(candidates) == 0
