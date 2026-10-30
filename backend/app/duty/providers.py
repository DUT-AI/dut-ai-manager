"""
Dishka Provider for Duty Module.
"""

from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.duty.application.check_overdue_duties_use_case import (
    CheckOverdueDutiesUseCase,
)
from app.duty.application.get_duties_use_case import GetDutiesUseCase
from app.duty.application.manage_duty_use_case import (
    DeleteDutyUseCase,
    RestoreDutyUseCase,
    UpdateDutyUseCase,
)
from app.duty.application.review_duty_use_case import (
    ApproveDutyUseCase,
    RejectDutyUseCase,
)
from app.duty.application.submit_duty_evidence_use_case import (
    SubmitDutyEvidenceUseCase,
)
from app.duty.application.toggle_duty_schedule_use_case import (
    BatchCreateDutyUseCase,
    ToggleDutyScheduleUseCase,
)
from app.duty.infrastructure.repository import DutyRepository
from app.duty.notification_handler import DutyNotificationHandler
from app.meeting.infrastructure.repository import MeetingRepository
from app.permission_request.infrastructure.repository import (
    PermissionRequestRepository,
)
from app.shared.domain.event_bus import EventBus
from app.shared.infrastructure.minio_service import MinioService
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository
from app.violation.application.create_violation_use_case import (
    CreateViolationUseCase,
)


class DutyModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_duty_repo(self, session: Session) -> DutyRepository:
        return DutyRepository(session)

    @provide
    def get_duties_use_case(
        self,
        duty_repo: DutyRepository,
        team_repo: TeamRepository,
        meeting_repo: MeetingRepository,
    ) -> GetDutiesUseCase:
        return GetDutiesUseCase(
            repo=duty_repo,
            team_repo=team_repo,
            meeting_repo=meeting_repo,
        )

    @provide
    def get_toggle_duty_schedule_use_case(
        self,
        duty_repo: DutyRepository,
        meeting_repo: MeetingRepository,
        team_repo: TeamRepository,
    ) -> ToggleDutyScheduleUseCase:
        return ToggleDutyScheduleUseCase(
            duty_repo=duty_repo,
            meeting_repo=meeting_repo,
            team_repo=team_repo,
            event_bus=EventBus,
        )

    @provide
    def get_batch_create_duty_use_case(
        self,
        duty_repo: DutyRepository,
        team_repo: TeamRepository,
    ) -> BatchCreateDutyUseCase:
        return BatchCreateDutyUseCase(
            duty_repo=duty_repo,
            team_repo=team_repo,
            event_bus=EventBus,
        )

    @provide
    def get_update_duty_use_case(
        self,
        duty_repo: DutyRepository,
        team_repo: TeamRepository,
    ) -> UpdateDutyUseCase:
        return UpdateDutyUseCase(
            duty_repo=duty_repo,
            team_repo=team_repo,
            event_bus=EventBus,
        )

    @provide
    def get_delete_duty_use_case(
        self,
        duty_repo: DutyRepository,
    ) -> DeleteDutyUseCase:
        return DeleteDutyUseCase(duty_repo=duty_repo)

    @provide
    def get_restore_duty_use_case(
        self,
        duty_repo: DutyRepository,
    ) -> RestoreDutyUseCase:
        return RestoreDutyUseCase(duty_repo=duty_repo)

    @provide
    def get_submit_duty_evidence_use_case(
        self,
        duty_repo: DutyRepository,
        team_repo: TeamRepository,
        minio_service: MinioService,
        meeting_repo: MeetingRepository,
    ) -> SubmitDutyEvidenceUseCase:
        return SubmitDutyEvidenceUseCase(
            duty_repo=duty_repo,
            team_repo=team_repo,
            minio_service=minio_service,
            meeting_repo=meeting_repo,
            event_bus=EventBus,
        )

    @provide
    def get_check_overdue_duties_use_case(
        self,
        duty_repo: DutyRepository,
        meeting_repo: MeetingRepository,
        team_repo: TeamRepository,
        create_violation_use_case: CreateViolationUseCase,
    ) -> CheckOverdueDutiesUseCase:
        return CheckOverdueDutiesUseCase(
            duty_repo=duty_repo,
            meeting_repo=meeting_repo,
            team_repo=team_repo,
            create_violation_use_case=create_violation_use_case,
            event_bus=EventBus,
        )

    @provide
    def get_approve_duty_use_case(
        self, duty_repo: DutyRepository
    ) -> ApproveDutyUseCase:
        return ApproveDutyUseCase(duty_repo=duty_repo, event_bus=EventBus)

    @provide
    def get_reject_duty_use_case(self, duty_repo: DutyRepository) -> RejectDutyUseCase:
        return RejectDutyUseCase(duty_repo=duty_repo, event_bus=EventBus)

    @provide
    def get_duty_notification_handler(
        self,
        dispatcher: UnifiedNotificationDispatcher,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        meeting_repo: MeetingRepository,
        duty_repo: DutyRepository,
        permission_repo: PermissionRequestRepository,
    ) -> DutyNotificationHandler:
        return DutyNotificationHandler(
            dispatcher=dispatcher,
            user_repo=user_repo,
            team_repo=team_repo,
            meeting_repo=meeting_repo,
            duty_repo=duty_repo,
            permission_repo=permission_repo,
        )
