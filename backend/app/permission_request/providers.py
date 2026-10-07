from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.homework.infrastructure.repository import HomeworkRepository
from app.meeting.infrastructure.repository import MeetingRepository
from app.permission_request.application.create_change_meeting_request_use_case import (
    CreateChangeMeetingRequestUseCase,
)
from app.permission_request.application.event_handlers import (
    MeetingParticipantTransferredNotificationHandler,
    PermissionRequestNotificationHandler,
)
from app.permission_request.application.use_cases import (
    CreatePermissionRequestUseCase,
    DeletePermissionRequestUseCase,
    GetPermissionRequestsUseCase,
    RestorePermissionRequestUseCase,
    UpdatePermissionRequestUseCase,
)
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.infrastructure.notification_service import NotificationService
from app.user.infrastructure.repository import UserRepository


class PermissionRequestModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_permission_repo(self, session: Session) -> PermissionRequestRepository:
        return PermissionRequestRepository(session)

    @provide
    def get_get_requests_uc(
        self, repo: PermissionRequestRepository
    ) -> GetPermissionRequestsUseCase:
        return GetPermissionRequestsUseCase(repo)

    @provide
    def get_create_request_uc(
        self,
        repo: PermissionRequestRepository,
        homework_repo: HomeworkRepository,
    ) -> CreatePermissionRequestUseCase:
        return CreatePermissionRequestUseCase(repo, homework_repo)

    @provide
    def get_create_change_meeting_request_uc(
        self,
        permission_repo: PermissionRequestRepository,
        meeting_repo: MeetingRepository,
    ) -> CreateChangeMeetingRequestUseCase:
        return CreateChangeMeetingRequestUseCase(
            permission_repo=permission_repo,
            meeting_repo=meeting_repo,
        )

    @provide
    def get_update_request_uc(
        self,
        repo: PermissionRequestRepository,
        homework_repo: HomeworkRepository,
    ) -> UpdatePermissionRequestUseCase:
        return UpdatePermissionRequestUseCase(repo, homework_repo)

    @provide
    def get_delete_request_uc(
        self, repo: PermissionRequestRepository
    ) -> DeletePermissionRequestUseCase:
        return DeletePermissionRequestUseCase(repo)

    @provide
    def get_restore_request_uc(
        self, repo: PermissionRequestRepository
    ) -> RestorePermissionRequestUseCase:
        return RestorePermissionRequestUseCase(repo)

    @provide
    def get_notification_handler(
        self,
        notification_service: NotificationService,
        user_repo: UserRepository,
    ) -> PermissionRequestNotificationHandler:
        return PermissionRequestNotificationHandler(
            notification_service=notification_service,
            user_repo=user_repo,
        )

    @provide
    def get_meeting_participant_transferred_notification_handler(
        self,
        notification_service: NotificationService,
        user_repo: UserRepository,
        meeting_repo: MeetingRepository,
    ) -> MeetingParticipantTransferredNotificationHandler:
        return MeetingParticipantTransferredNotificationHandler(
            notification_service=notification_service,
            user_repo=user_repo,
            meeting_repo=meeting_repo,
        )

