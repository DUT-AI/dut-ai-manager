from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.homework.infrastructure.repository import HomeworkRepository
from app.permission_request.application.event_handlers import (
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
from app.shared.infrastructure.discord_service import DiscordService
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
        discord_service: DiscordService,
        user_repo: UserRepository,
    ) -> PermissionRequestNotificationHandler:
        return PermissionRequestNotificationHandler(
            discord_service=discord_service,
            user_repo=user_repo,
        )
