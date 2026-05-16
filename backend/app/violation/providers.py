from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.infrastructure.discord_service import DiscordService
from app.user.infrastructure.repository import UserRepository
from app.violation.application.event_handlers import AutomatedViolationHandler
from app.violation.application.use_cases import CreateViolationUseCase
from app.violation.infrastructure.repository import ViolationRepository
from app.violation.notification_handler import ViolationNotificationHandler
from app.violation.permission_handler import PermissionViolationHandler
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient


class ViolationModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_violation_repo(self, session: Session) -> ViolationRepository:
        return ViolationRepository(session)

    @provide
    def create_violation_uc(self, repo: ViolationRepository) -> CreateViolationUseCase:
        return CreateViolationUseCase(repo)

    @provide
    def get_permission_handler(
        self,
        create_violation_uc: CreateViolationUseCase,
        permission_repo: PermissionRequestRepository,
    ) -> PermissionViolationHandler:
        return PermissionViolationHandler(create_violation_uc, permission_repo)

    @provide
    def get_automated_violation_handler(
        self,
        create_violation_uc: CreateViolationUseCase,
        permission_repo: PermissionRequestRepository,
    ) -> AutomatedViolationHandler:
        return AutomatedViolationHandler(create_violation_uc, permission_repo)

    @provide
    def get_violation_notification_handler(
        self,
        discord_service: DiscordService,
        zalo_bot: ZaloBotClient,
        user_repo: UserRepository,
    ) -> ViolationNotificationHandler:
        return ViolationNotificationHandler(discord_service, zalo_bot, user_repo)
