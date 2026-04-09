from dishka import Provider, Scope, provide
from sqlmodel import Session
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.permission_request.application.event_handlers import PermissionRequestNotificationHandler
from app.shared.infrastructure.discord_service import DiscordService
from app.user.infrastructure.repository import UserRepository

class PermissionRequestModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_permission_repo(self, session: Session) -> PermissionRequestRepository:
        return PermissionRequestRepository(session)

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
