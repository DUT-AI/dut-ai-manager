from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.homework.application.event_handlers import (
    HomeworkNotificationHandler,
)
from app.homework.application.use_cases import (
    HomeworkUseCases,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import (
    HomeworkRepository,
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
    def get_quiz_api_client(self) -> QuizApiClient:
        return QuizApiClient()

    @provide
    def get_homework_repo(self, session: Session) -> HomeworkRepository:
        return HomeworkRepository(session)

    @provide
    def get_use_cases(
        self,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        minio_service: MinioService,
        quiz_api: QuizApiClient,
    ) -> HomeworkUseCases:
        return HomeworkUseCases(
            homework_repo=homework_repo,
            user_repo=user_repo,
            team_repo=team_repo,
            minio_service=minio_service,
            quiz_api=quiz_api,
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

