"""
Unit tests for Reminder and Notification Use Cases with Unified Architecture.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.duty.domain.entity import CleaningDuty, DutyStatus
from app.homework.domain.entity import Homework, HomeworkSubmission
from app.meeting.domain.entity import Meeting, MeetingParticipant
from app.meeting.domain.value_objects import ParticipantRole, ParticipantStatus
from app.reminder.application.get_my_notifications_use_case import (
    GetMyNotificationsUseCase,
)
from app.reminder.application.get_unread_notification_count_use_case import (
    GetUnreadNotificationCountUseCase,
)
from app.reminder.application.mark_all_notifications_as_read_use_case import (
    MarkAllNotificationsAsReadUseCase,
)
from app.reminder.application.mark_notification_as_read_use_case import (
    MarkNotificationAsReadUseCase,
)
from app.reminder.application.reminder_dispatcher import ReminderDispatcher
from app.reminder.application.scan_and_send_reminders_use_case import (
    ScanAndSendRemindersUseCase,
)
from app.reminder.application.scanners.duty_scanner import DutyTaskScanner
from app.reminder.application.scanners.homework_scanner import HomeworkTaskScanner
from app.reminder.application.scanners.meeting_evaluation_scanner import (
    MeetingEvaluationTaskScanner,
)
from app.reminder.application.scanners.upcoming_meeting_scanner import (
    UpcomingMeetingTaskScanner,
)
from app.reminder.domain.entity import (
    Notification,
    NotificationCategory,
    NotificationLevel,
    ReminderStage,
    ReminderStatus,
    TaskType,
)
from app.shared.infrastructure.notification.channel import (
    ChannelDeliveryResult,
    ChannelType,
    DispatchResult,
)


@pytest.fixture
def mock_notification_repo():
    return MagicMock()


@pytest.fixture
def sample_notification():
    return Notification(
        id=1,
        user_id=10,
        title="Nhắc nhở bài tập",
        content="Nội dung nhắc nhở",
        category=NotificationCategory.HOMEWORK,
        level=NotificationLevel.WARNING,
        action_url="/dashboard/my-homeworks",
        is_read=False,
        created_at=datetime(2026, 10, 21, 10, 0, 0),
    )


@pytest.mark.asyncio
async def test_get_my_notifications_use_case(
    mock_notification_repo, sample_notification
):
    mock_notification_repo.get_user_notifications.return_value = (
        [sample_notification],
        1,
    )
    use_case = GetMyNotificationsUseCase(mock_notification_repo)

    items, total = await use_case.execute(user_id=10, page=1, page_size=20)

    assert total == 1
    assert len(items) == 1
    assert items[0].id == 1
    assert items[0].title == "Nhắc nhở bài tập"
    mock_notification_repo.get_user_notifications.assert_called_once_with(
        user_id=10, category=None, is_read=None, page=1, page_size=20
    )


@pytest.mark.asyncio
async def test_get_unread_notification_count_use_case(mock_notification_repo):
    mock_notification_repo.get_unread_count.return_value = 5
    use_case = GetUnreadNotificationCountUseCase(mock_notification_repo)

    res = await use_case.execute(user_id=10)

    assert res.unread_count == 5
    mock_notification_repo.get_unread_count.assert_called_once_with(user_id=10)


@pytest.mark.asyncio
async def test_mark_notification_as_read_use_case(
    mock_notification_repo, sample_notification
):
    sample_notification.is_read = True
    mock_notification_repo.mark_as_read.return_value = sample_notification
    use_case = MarkNotificationAsReadUseCase(mock_notification_repo)

    res = await use_case.execute(notification_id=1, user_id=10)

    assert res is not None
    assert res.is_read is True
    mock_notification_repo.mark_as_read.assert_called_once_with(
        notification_id=1, user_id=10
    )


@pytest.mark.asyncio
async def test_mark_all_notifications_as_read_use_case(mock_notification_repo):
    mock_notification_repo.mark_all_as_read.return_value = 3
    use_case = MarkAllNotificationsAsReadUseCase(mock_notification_repo)

    res = await use_case.execute(user_id=10)

    assert res == 3
    mock_notification_repo.mark_all_as_read.assert_called_once_with(user_id=10)


@pytest.mark.asyncio
async def test_scan_and_send_reminders_homework_dry_run():
    # Setup mocks
    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()
    notif_repo = MagicMock()
    user_repo = MagicMock()
    MagicMock()
    MagicMock()

    from zoneinfo import ZoneInfo

    from app.homework.infrastructure.homework_assignee_repository import (
        AssigneeUserInfo,
    )

    now = datetime(
        2026, 10, 20, 23, 59, 59
    )  # Đúng 24 giờ trước deadline 2026-10-21 23:59:59 -> Khớp duy nhất OFFSET_1D
    deadline_dt = datetime(
        2026, 10, 21, 23, 59, 59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")
    )

    mock_hw = Homework(
        id=100,
        title="Bài tập Python OOP",
    )
    hw_repo.get_all.return_value = [mock_hw]
    hw_assignee_repo.get_assignees_with_user_info.return_value = [
        AssigneeUserInfo(
            user_id=1, name="User 1", avatar_url=None, deadline=deadline_dt
        ),
        AssigneeUserInfo(
            user_id=2, name="User 2", avatar_url=None, deadline=deadline_dt
        ),
    ]
    hw_sub_repo.get_submissions_by_user.return_value = []  # Chưa nộp
    notif_repo.has_reminder_been_sent.return_value = False
    notif_repo.get_last_reminder_time.return_value = None

    homework_scanner = HomeworkTaskScanner(
        homework_repo=hw_repo,
        homework_assignee_repo=hw_assignee_repo,
        homework_submission_repo=hw_sub_repo,
    )
    mock_unified_dispatcher = MagicMock()
    mock_unified_dispatcher.dispatch = AsyncMock(
        return_value=DispatchResult(
            success=True,
            user_id=1,
            in_app=ChannelDeliveryResult(
                channel=ChannelType.IN_APP, success=True, status="SAVED"
            ),
            queued=True,
        )
    )
    dispatcher = ReminderDispatcher(
        notification_repo=notif_repo,
        user_repo=user_repo,
        unified_dispatcher=mock_unified_dispatcher,
    )

    use_case = ScanAndSendRemindersUseCase(
        scanners=[homework_scanner],
        dispatcher=dispatcher,
        notification_repo=notif_repo,
    )

    result = await use_case.execute(dry_run=True, now=now)

    assert result.total_tasks_scanned >= 1
    assert result.total_reminders_sent == 2  # 2 users
    assert result.total_skipped_already_sent == 0
    assert len(result.details) == 2
    assert result.details[0].stage == ReminderStage.OFFSET_1D


@pytest.mark.asyncio
async def test_duty_task_scanner():
    duty_repo = MagicMock()
    team_repo = MagicMock()

    # 1. Lúc 18:00 (cách deadline 22:00 đúng 4 tiếng) -> Khớp mốc OFFSET_4H
    now_4h = datetime(2026, 10, 21, 18, 0, 0)
    today_date = now_4h.date()

    mock_duty = CleaningDuty(
        id=50,
        duty_date=today_date,
        team_id=1,
        status=DutyStatus.PENDING,
    )
    duty_repo.get_pending_duties_for_date.return_value = [mock_duty]
    team_repo.get_user_ids_by_teams.return_value = [101, 102]

    scanner = DutyTaskScanner(duty_repo=duty_repo, team_repo=team_repo)
    candidates_4h = scanner.scan_pending_tasks(now=now_4h)

    assert len(candidates_4h) == 2
    assert candidates_4h[0].user_id == 101
    assert candidates_4h[0].task_type == TaskType.DUTY
    assert candidates_4h[0].task_id == 50
    assert ReminderStage.OFFSET_4H in candidates_4h[0].stages

    # 2. Lúc 19:30 (khung giờ cố định cũ) -> Không còn mốc FIXED_1930, không sinh ứng viên
    now_1930 = datetime(2026, 10, 21, 19, 30, 0)
    candidates_1930 = scanner.scan_pending_tasks(now=now_1930)
    assert len(candidates_1930) == 0


@pytest.mark.asyncio
async def test_reminder_dispatcher_dispatch_success():
    notif_repo = MagicMock()
    user_repo = MagicMock()
    mock_unified_dispatcher = MagicMock()
    mock_unified_dispatcher.dispatch = AsyncMock(
        return_value=DispatchResult(
            success=True,
            user_id=1,
            in_app=ChannelDeliveryResult(
                channel=ChannelType.IN_APP, success=True, status="SAVED"
            ),
            queued=True,
        )
    )

    mock_user = MagicMock()
    mock_user.id = 10
    mock_user.discord_id = "123456789012345678"
    user_repo.get_by_id.return_value = mock_user

    dispatcher = ReminderDispatcher(
        notification_repo=notif_repo,
        user_repo=user_repo,
        unified_dispatcher=mock_unified_dispatcher,
    )

    now = datetime(2026, 10, 21, 20, 0, 0)
    deadline = datetime(2026, 10, 21, 23, 59, 59)

    status = await dispatcher.dispatch(
        task_type=TaskType.HOMEWORK,
        task_id=101,
        task_title="Test Bài Tập",
        user_id=10,
        deadline=deadline,
        stage=ReminderStage.OFFSET_4H,
        action_url="/dashboard/my-homeworks",
        now=now,
    )

    assert status == ReminderStatus.SENT
    mock_unified_dispatcher.dispatch.assert_called_once()
    payload = mock_unified_dispatcher.dispatch.call_args.args[0]
    assert payload.user_id == 10
    assert payload.task_type == "HOMEWORK"
    assert payload.task_id == 101


@pytest.mark.asyncio
async def test_meeting_evaluation_task_scanner():
    meeting_repo = MagicMock()
    eval_repo = MagicMock()

    now = datetime(2026, 10, 21, 19, 0, 0)
    meeting_start = datetime(2026, 10, 20, 18, 0, 0)
    meeting_end = datetime(2026, 10, 20, 20, 0, 0)

    mock_meeting = Meeting(
        id=77,
        title="Họp Lab & Báo Cáo Tiến Độ",
        start_time=meeting_start,
        end_time=meeting_end,
        enable_evaluation=True,
        participants=[
            MeetingParticipant(user_id=10, role=ParticipantRole.TRAINER),
            MeetingParticipant(
                user_id=1,
                role=ParticipantRole.TRAINEE,
                status=ParticipantStatus.COMPLETED,
            ),
            MeetingParticipant(
                user_id=2, role=ParticipantRole.TRAINEE, status=ParticipantStatus.JOINED
            ),
            MeetingParticipant(
                user_id=3,
                role=ParticipantRole.TRAINEE,
                status=ParticipantStatus.NOT_JOINED,
            ),
        ],
    )
    meeting_repo.get_all_with_participants.return_value = [mock_meeting]

    eval_repo.count_evaluations_by_reviewer.side_effect = (
        lambda meeting_id, reviewer_id: 1 if reviewer_id == 1 else 0
    )
    overall_repo = MagicMock()
    overall_repo.exists_for_meeting.return_value = True

    scanner = MeetingEvaluationTaskScanner(
        meeting_repo=meeting_repo,
        evaluation_repo=eval_repo,
        overall_eval_repo=overall_repo,
    )
    candidates = scanner.scan_pending_tasks(now=now)

    assert len(candidates) == 1
    assert candidates[0].user_id == 2
    assert candidates[0].task_type == TaskType.MEETING_EVALUATION
    assert candidates[0].task_id == 77
    assert ReminderStage.OFFSET_1H in candidates[0].stages


@pytest.mark.asyncio
async def test_scan_and_send_reminders_use_case_with_upcoming_meeting():
    meeting_repo = MagicMock()
    notification_repo = MagicMock()
    dispatcher = MagicMock()
    dispatcher.dispatch = AsyncMock(return_value=ReminderStatus.SENT)

    now = datetime(2026, 10, 21, 14, 0, 0)
    meeting_start = now + timedelta(hours=1)
    meeting_end = meeting_start + timedelta(hours=2)

    mock_meeting = Meeting(
        id=88,
        title="Họp Khởi Động Dự Án Mới",
        start_time=meeting_start,
        end_time=meeting_end,
        participants=[
            MeetingParticipant(
                user_id=5, status=ParticipantStatus.NOT_JOINED, is_deleted=False
            ),
            MeetingParticipant(
                user_id=6, status=ParticipantStatus.ABSENT_EXCUSED, is_deleted=False
            ),
        ],
    )
    meeting_repo.get_all_with_participants.return_value = [mock_meeting]

    # Chưa từng gửi và không trong cooldown
    notification_repo.has_reminder_been_sent.return_value = False
    notification_repo.get_last_reminder_time.return_value = None

    upcoming_scanner = UpcomingMeetingTaskScanner(meeting_repo=meeting_repo)
    use_case = ScanAndSendRemindersUseCase(
        scanners=[upcoming_scanner],
        dispatcher=dispatcher,
        notification_repo=notification_repo,
    )

    response = await use_case.execute(dry_run=False, now=now)

    assert response.total_tasks_scanned == 1
    assert response.total_reminders_sent == 1
    assert response.total_skipped_already_sent == 0
    assert response.total_failed == 0
    assert len(response.details) == 1
    assert response.details[0].task_type == TaskType.MEETING
    assert response.details[0].task_id == 88
    assert response.details[0].user_id == 5
    assert response.details[0].status == ReminderStatus.SENT

    dispatcher.dispatch.assert_called_once()


def test_homework_scanner_incomplete_submission_still_reminds():
    """Học sinh mới nộp Game nhưng chưa hoàn thành Coding thì scanner vẫn phải trả về candidate."""
    from zoneinfo import ZoneInfo

    from app.homework.infrastructure.homework_assignee_repository import (
        AssigneeUserInfo,
    )

    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()

    vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime(2026, 10, 20, 23, 59, 59, tzinfo=vn_tz)
    deadline_dt = datetime(2026, 10, 21, 23, 59, 59, tzinfo=vn_tz)

    # Bài tập yêu cầu cả Coding và Game
    mock_hw = Homework(
        id=101,
        title="Bài tập thuật toán",
        requires_coding=True,
        requires_game=True,
    )
    hw_repo.get_all.return_value = [mock_hw]
    hw_assignee_repo.get_assignees_with_user_info.return_value = [
        AssigneeUserInfo(
            user_id=10, name="Học viên 10", avatar_url=None, deadline=deadline_dt
        ),
    ]

    # Học sinh chỉ mới nộp Game, chưa có bài nộp Coding
    hw_sub_repo.get_submissions_by_user.return_value = [
        HomeworkSubmission.create_game(
            homework_id=101,
            user_id=10,
            submitted_at=now,
            score=100.0,
            is_passed=True,
        )
    ]

    scanner = HomeworkTaskScanner(
        homework_repo=hw_repo,
        homework_assignee_repo=hw_assignee_repo,
        homework_submission_repo=hw_sub_repo,
    )

    candidates = scanner.scan_pending_tasks(now=now)
    assert len(candidates) == 1
    assert candidates[0].user_id == 10
    assert candidates[0].task_id == 101


def test_homework_scanner_failed_submission_still_reminds():
    """Học sinh nộp bài Coding nhưng bị Failed (chưa pass) thì scanner vẫn phải trả về candidate."""
    from zoneinfo import ZoneInfo

    from app.homework.infrastructure.homework_assignee_repository import (
        AssigneeUserInfo,
    )

    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()

    vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime(2026, 10, 20, 23, 59, 59, tzinfo=vn_tz)
    deadline_dt = datetime(2026, 10, 21, 23, 59, 59, tzinfo=vn_tz)

    mock_hw = Homework(
        id=102,
        title="Bài tập Python cơ bản",
        requires_coding=True,
        requires_game=False,
    )
    hw_repo.get_all.return_value = [mock_hw]
    hw_assignee_repo.get_assignees_with_user_info.return_value = [
        AssigneeUserInfo(
            user_id=20, name="Học viên 20", avatar_url=None, deadline=deadline_dt
        ),
    ]

    # Nộp bài nhưng is_passed = False
    hw_sub_repo.get_submissions_by_user.return_value = [
        HomeworkSubmission.create_coding(
            homework_id=102,
            user_id=20,
            exercise_id="ex1",
            submitted_at=now,
            is_passed=False,
        )
    ]

    scanner = HomeworkTaskScanner(
        homework_repo=hw_repo,
        homework_assignee_repo=hw_assignee_repo,
        homework_submission_repo=hw_sub_repo,
    )

    candidates = scanner.scan_pending_tasks(now=now)
    assert len(candidates) == 1
    assert candidates[0].user_id == 20


def test_homework_scanner_fully_completed_skips():
    """Học sinh đã nộp đủ cả Coding (passed) và Game thì scanner phải bỏ qua."""
    from zoneinfo import ZoneInfo

    from app.homework.infrastructure.homework_assignee_repository import (
        AssigneeUserInfo,
    )

    hw_repo = MagicMock()
    hw_assignee_repo = MagicMock()
    hw_sub_repo = MagicMock()

    vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime(2026, 10, 20, 23, 59, 59, tzinfo=vn_tz)
    deadline_dt = datetime(2026, 10, 21, 23, 59, 59, tzinfo=vn_tz)

    mock_hw = Homework(
        id=103,
        title="Bài tập hoàn chỉnh",
        requires_coding=True,
        requires_game=True,
    )
    hw_repo.get_all.return_value = [mock_hw]
    hw_assignee_repo.get_assignees_with_user_info.return_value = [
        AssigneeUserInfo(
            user_id=30, name="Học viên 30", avatar_url=None, deadline=deadline_dt
        ),
    ]

    # Đã nộp cả Game và Coding passed
    hw_sub_repo.get_submissions_by_user.return_value = [
        HomeworkSubmission.create_game(
            homework_id=103,
            user_id=30,
            submitted_at=now,
            score=100.0,
            is_passed=True,
        ),
        HomeworkSubmission.create_coding(
            homework_id=103,
            user_id=30,
            exercise_id="ex1",
            submitted_at=now,
            is_passed=True,
        ),
    ]

    scanner = HomeworkTaskScanner(
        homework_repo=hw_repo,
        homework_assignee_repo=hw_assignee_repo,
        homework_submission_repo=hw_sub_repo,
    )

    candidates = scanner.scan_pending_tasks(now=now)
    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_reminder_dispatcher_dispatch_failure():
    notif_repo = MagicMock()
    user_repo = MagicMock()
    mock_unified_dispatcher = MagicMock()
    mock_unified_dispatcher.dispatch = AsyncMock(
        return_value=DispatchResult(
            success=False,
            user_id=10,
            in_app=ChannelDeliveryResult(
                channel=ChannelType.IN_APP,
                success=False,
                status="FAILED",
                error_message="DB error",
            ),
            queued=False,
            error_message="DB error",
        )
    )

    mock_user = MagicMock()
    mock_user.id = 10
    mock_user.discord_id = None
    user_repo.get_by_id.return_value = mock_user

    dispatcher = ReminderDispatcher(
        notification_repo=notif_repo,
        user_repo=user_repo,
        unified_dispatcher=mock_unified_dispatcher,
    )

    now = datetime(2026, 10, 21, 20, 0, 0)
    deadline = datetime(2026, 10, 21, 23, 59, 59)

    status = await dispatcher.dispatch(
        task_type=TaskType.HOMEWORK,
        task_id=101,
        task_title="Test Bài Tập",
        user_id=10,
        deadline=deadline,
        stage=ReminderStage.OFFSET_4H,
        action_url="/dashboard/my-homeworks",
        now=now,
    )

    assert status == ReminderStatus.FAILED


def test_calculate_matching_stages_pure_countdown_offsets():
    """Kiểm tra calculate_matching_stages chỉ trả về 3 mốc đếm ngược: 24h, 4h, 1h."""
    now = datetime(2026, 11, 4, 10, 0, 0)

    # 1. Mốc 24h (khoảng 22.0h - 26.0h)
    dl_24h = now + timedelta(hours=24)
    stages = ReminderStage.calculate_matching_stages(deadline=dl_24h, now=now)
    assert stages == [ReminderStage.OFFSET_1D]

    # 2. Mốc 4h (khoảng 3.5h - 4.5h)
    dl_4h = now + timedelta(hours=4)
    stages = ReminderStage.calculate_matching_stages(deadline=dl_4h, now=now)
    assert stages == [ReminderStage.OFFSET_4H]

    # 3. Mốc 1h (khoảng 0.5h - 1.5h)
    dl_1h = now + timedelta(hours=1)
    stages = ReminderStage.calculate_matching_stages(deadline=dl_1h, now=now)
    assert stages == [ReminderStage.OFFSET_1H]

    # 4. Mốc 48h cũ (OFFSET_2D đã bị loại bỏ)
    dl_48h = now + timedelta(hours=48)
    stages = ReminderStage.calculate_matching_stages(deadline=dl_48h, now=now)
    assert stages == []

    # 5. Mốc 12h cũ (OFFSET_12H đã bị loại bỏ)
    dl_12h = now + timedelta(hours=12)
    stages = ReminderStage.calculate_matching_stages(deadline=dl_12h, now=now)
    assert stages == []


def test_calculate_matching_stages_no_fixed_hours():
    """Kiểm tra vào các khung giờ cố định cũ (08:00, 12:00, 19:30, 22:00) không sinh mốc cố định nếu deadline không khớp mốc đếm ngược."""
    # 08:00 sáng, deadline cách 8 tiếng (16:00) -> diff_hours = 8.0 -> []
    now_0800 = datetime(2026, 11, 4, 8, 0, 0)
    dl_0800 = now_0800 + timedelta(hours=8)
    assert ReminderStage.calculate_matching_stages(deadline=dl_0800, now=now_0800) == []

    # 12:00 trưa, deadline cách 8 tiếng (20:00) -> diff_hours = 8.0 -> []
    now_1200 = datetime(2026, 11, 4, 12, 0, 0)
    dl_1200 = now_1200 + timedelta(hours=8)
    assert ReminderStage.calculate_matching_stages(deadline=dl_1200, now=now_1200) == []

    # 19:30 tối, deadline cách 8 tiếng (03:30) -> diff_hours = 8.0 -> []
    now_1930 = datetime(2026, 11, 4, 19, 30, 0)
    dl_1930 = now_1930 + timedelta(hours=8)
    assert ReminderStage.calculate_matching_stages(deadline=dl_1930, now=now_1930) == []

    # 22:00 đêm, deadline cách 8 tiếng (06:00) -> diff_hours = 8.0 -> []
    now_2200 = datetime(2026, 11, 4, 22, 0, 0)
    dl_2200 = now_2200 + timedelta(hours=8)
    assert ReminderStage.calculate_matching_stages(deadline=dl_2200, now=now_2200) == []


def test_reminder_stage_is_critical():
    """Kiểm tra chỉ có OFFSET_1H là critical, các mốc khác không phải critical."""
    assert ReminderStage.OFFSET_1H.is_critical is True
    assert ReminderStage.OFFSET_4H.is_critical is False
    assert ReminderStage.OFFSET_1D.is_critical is False
    assert ReminderStage.FIXED_2200.is_critical is False


def test_zalo_channel_excluded_from_dispatcher_external_channels():
    """Kiểm tra UnifiedNotificationDispatcher loại Zalo khỏi _external_channels để chống spam người dùng."""
    from app.shared.infrastructure.notification.dispatcher import (
        UnifiedNotificationDispatcher,
    )

    mock_user_repo = MagicMock()
    mock_in_app = MagicMock()
    mock_discord = MagicMock()
    mock_zalo = MagicMock()
    mock_web_push = MagicMock()

    dispatcher = UnifiedNotificationDispatcher(
        user_repo=mock_user_repo,
        in_app_channel=mock_in_app,
        discord_channel=mock_discord,
        zalo_channel=mock_zalo,
        web_push_channel=mock_web_push,
    )

    assert mock_zalo not in dispatcher._external_channels
    assert dispatcher._external_channels == [mock_discord, mock_web_push]
