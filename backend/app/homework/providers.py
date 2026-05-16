from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.homework.application.event_handlers import (
    HomeworkGradedNotificationHandler,
    HomeworkNotificationHandler,
)
from app.homework.application.use_cases import (
    CheckOverdueHomeworkUseCase,
    HomeworkUseCases,
)
from app.homework.infrastructure.repository import (
    HomeworkRepository,
    HomeworkSubmissionRepository,
)
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.infrastructure.discord_service import DiscordService
from app.shared.infrastructure.minio_service import MinioService
from app.team.infrastructure.repository import TeamRepository
from app.user.infrastructure.repository import UserRepository
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient


class HomeworkModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_homework_repo(self, session: Session) -> HomeworkRepository:
        return HomeworkRepository(session)

    @provide
    def get_submission_repo(self, session: Session) -> HomeworkSubmissionRepository:
        return HomeworkSubmissionRepository(session)

    @provide
    def get_use_cases(
        self,
        homework_repo: HomeworkRepository,
        submission_repo: HomeworkSubmissionRepository,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        minio_service: MinioService,
    ) -> HomeworkUseCases:
        return HomeworkUseCases(
            homework_repo=homework_repo,
            submission_repo=submission_repo,
            user_repo=user_repo,
            team_repo=team_repo,
            minio_service=minio_service,
        )

    @provide
    def get_check_overdue_use_case(
        self,
        submission_repo: HomeworkSubmissionRepository,
        permission_repo: PermissionRequestRepository,
    ) -> CheckOverdueHomeworkUseCase:
        return CheckOverdueHomeworkUseCase(
            submission_repo=submission_repo,
            permission_repo=permission_repo,
        )

    @provide
    def get_notification_handler(
        self,
        discord_service: DiscordService,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        zalo_bot: ZaloBotClient,
    ) -> HomeworkNotificationHandler:
        return HomeworkNotificationHandler(
            discord_service, homework_repo, user_repo, zalo_bot
        )

    @provide
    def get_graded_notification_handler(
        self,
        discord_service: DiscordService,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        zalo_bot: ZaloBotClient,
    ) -> HomeworkGradedNotificationHandler:
        return HomeworkGradedNotificationHandler(
            discord_service, homework_repo, user_repo, zalo_bot
        )
