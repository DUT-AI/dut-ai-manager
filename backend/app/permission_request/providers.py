from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.duty.infrastructure.repository import DutyRepository
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.meeting.infrastructure.repository import MeetingRepository
from app.permission_request.application import (
    CreatePermissionRequestUseCase,
    DeletePermissionRequestUseCase,
    GetPermissionRequestDetailUseCase,
    GetPermissionRequestsUseCase,
    RestorePermissionRequestUseCase,
    UpdatePermissionRequestUseCase,
)
from app.permission_request.application.event_handlers import (
    MeetingParticipantTransferredNotificationHandler,
    PermissionRequestNotificationHandler,
)
from app.permission_request.application.strategies import (
    AbsenceStrategy,
    ChangeMeetingStrategy,
    LateStrategy,
    OtherStrategy,
    PermissionStrategyRegistry,
    PostponeStrategy,
)
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.user.infrastructure.repository import UserRepository


class PermissionRequestModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_permission_repo(self, session: Session) -> PermissionRequestRepository:
        return PermissionRequestRepository(session)

    @provide
    def get_strategy_registry(
        self,
        repo: PermissionRequestRepository,
        meeting_repo: MeetingRepository,
        homework_repo: HomeworkRepository,
    ) -> PermissionStrategyRegistry:
        strategies = [
            AbsenceStrategy(repo, meeting_repo),
            LateStrategy(repo, meeting_repo),
            PostponeStrategy(homework_repo),
            ChangeMeetingStrategy(repo, meeting_repo),
            OtherStrategy(),
        ]
        return PermissionStrategyRegistry(strategies)

    @provide
    def get_get_requests_uc(
        self, repo: PermissionRequestRepository
    ) -> GetPermissionRequestsUseCase:
        return GetPermissionRequestsUseCase(repo)

    @provide
    def get_get_request_detail_uc(
        self,
        repo: PermissionRequestRepository,
        meeting_repo: MeetingRepository,
        homework_repo: HomeworkRepository,
    ) -> GetPermissionRequestDetailUseCase:
        return GetPermissionRequestDetailUseCase(
            repo=repo,
            meeting_repo=meeting_repo,
            homework_repo=homework_repo,
        )

    @provide
    def get_create_request_uc(
        self,
        repo: PermissionRequestRepository,
        strategy_registry: PermissionStrategyRegistry,
    ) -> CreatePermissionRequestUseCase:
        return CreatePermissionRequestUseCase(
            repo=repo,
            strategy_registry=strategy_registry,
        )

    @provide
    def get_update_request_uc(
        self,
        repo: PermissionRequestRepository,
    ) -> UpdatePermissionRequestUseCase:
        return UpdatePermissionRequestUseCase(repo)

    @provide
    def get_delete_request_uc(
        self,
        repo: PermissionRequestRepository,
        strategy_registry: PermissionStrategyRegistry,
    ) -> DeletePermissionRequestUseCase:
        return DeletePermissionRequestUseCase(
            repo=repo,
            strategy_registry=strategy_registry,
        )

    @provide
    def get_restore_request_uc(
        self, repo: PermissionRequestRepository
    ) -> RestorePermissionRequestUseCase:
        return RestorePermissionRequestUseCase(repo)

    @provide
    def get_notification_handler(
        self,
        dispatcher: UnifiedNotificationDispatcher,
        user_repo: UserRepository,
    ) -> PermissionRequestNotificationHandler:
        return PermissionRequestNotificationHandler(
            dispatcher=dispatcher,
            user_repo=user_repo,
        )

    @provide
    def get_meeting_participant_transferred_notification_handler(
        self,
        dispatcher: UnifiedNotificationDispatcher,
        user_repo: UserRepository,
        meeting_repo: MeetingRepository,
        duty_repo: DutyRepository,
    ) -> MeetingParticipantTransferredNotificationHandler:
        return MeetingParticipantTransferredNotificationHandler(
            dispatcher=dispatcher,
            user_repo=user_repo,
            meeting_repo=meeting_repo,
            duty_repo=duty_repo,
        )
