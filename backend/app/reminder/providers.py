"""
Reminder & Notification Dishka Provider.
"""

from collections.abc import AsyncIterable
from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.duty.infrastructure.repository import DutyRepository
from app.homework.infrastructure.homework_assignee_repository import HomeworkAssigneeRepository
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingRepository,
)
from app.reminder.application.get_my_notifications_use_case import GetMyNotificationsUseCase
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
from app.reminder.application.scanners.duty_scanner import DutyTaskScanner
from app.reminder.application.scanners.homework_scanner import HomeworkTaskScanner
from app.reminder.application.scanners.meeting_evaluation_scanner import (
    MeetingEvaluationTaskScanner,
)
from app.reminder.application.scan_and_send_reminders_use_case import (
    ScanAndSendRemindersUseCase,
)
from app.reminder.infrastructure.repository import NotificationRepository
from app.shared.infrastructure.discord_service import DiscordService
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository


class ReminderModuleProvider(Provider):
    scope = Scope.REQUEST

    # Repository
    @provide
    def get_notification_repo(self, session: Session) -> NotificationRepository:
        return NotificationRepository(session)

    # Use Cases
    @provide
    def get_my_notifications_use_case(
        self, repo: NotificationRepository
    ) -> GetMyNotificationsUseCase:
        return GetMyNotificationsUseCase(repo)

    @provide
    def get_unread_count_use_case(
        self, repo: NotificationRepository
    ) -> GetUnreadNotificationCountUseCase:
        return GetUnreadNotificationCountUseCase(repo)

    @provide
    def mark_read_use_case(
        self, repo: NotificationRepository
    ) -> MarkNotificationAsReadUseCase:
        return MarkNotificationAsReadUseCase(repo)

    @provide
    def mark_all_read_use_case(
        self, repo: NotificationRepository
    ) -> MarkAllNotificationsAsReadUseCase:
        return MarkAllNotificationsAsReadUseCase(repo)

    # Scanners & Dispatcher
    @provide
    def get_homework_scanner(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
    ) -> HomeworkTaskScanner:
        return HomeworkTaskScanner(
            homework_repo=homework_repo,
            homework_assignee_repo=homework_assignee_repo,
            homework_submission_repo=homework_submission_repo,
        )

    @provide
    def get_duty_scanner(
        self,
        duty_repo: DutyRepository,
        team_repo: TeamRepository,
    ) -> DutyTaskScanner:
        return DutyTaskScanner(
            duty_repo=duty_repo,
            team_repo=team_repo,
        )

    @provide
    def get_meeting_evaluation_scanner(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
    ) -> MeetingEvaluationTaskScanner:
        return MeetingEvaluationTaskScanner(
            meeting_repo=meeting_repo,
            evaluation_repo=evaluation_repo,
        )

    @provide
    def get_reminder_dispatcher(
        self,
        notification_repo: NotificationRepository,
        user_repo: UserRepository,
        discord_service: DiscordService,
    ) -> ReminderDispatcher:
        return ReminderDispatcher(
            notification_repo=notification_repo,
            user_repo=user_repo,
            discord_service=discord_service,
        )

    @provide
    def scan_and_send_reminders_use_case(
        self,
        homework_scanner: HomeworkTaskScanner,
        duty_scanner: DutyTaskScanner,
        meeting_evaluation_scanner: MeetingEvaluationTaskScanner,
        dispatcher: ReminderDispatcher,
        notification_repo: NotificationRepository,
    ) -> ScanAndSendRemindersUseCase:
        return ScanAndSendRemindersUseCase(
            scanners=[homework_scanner, duty_scanner, meeting_evaluation_scanner],
            dispatcher=dispatcher,
            notification_repo=notification_repo,
        )
