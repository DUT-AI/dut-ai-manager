from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.homework.application import (
    CheckOverdueHomeworkUseCase,
    CreateHomeworkUseCase,
    DeleteHomeworkUseCase,
    GetHomeworkSubmissionStatusUseCase,
    GetHomeworksUseCase,
    RescanAllHomeworksUseCase,
    UpdateHomeworkUseCase,
)
from app.homework.application.event_handlers import (
    HomeworkNotificationHandler,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import (
    HomeworkRepository,
)
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.infrastructure.discord_service import DiscordService
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
    def get_get_homeworks_use_case(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
    ) -> GetHomeworksUseCase:
        return GetHomeworksUseCase(
            homework_repo=homework_repo,
            quiz_api=quiz_api,
            user_repo=user_repo,
        )

    @provide
    def get_create_homework_use_case(
        self,
        homework_repo: HomeworkRepository,
    ) -> CreateHomeworkUseCase:
        return CreateHomeworkUseCase(
            homework_repo=homework_repo,
        )

    @provide
    def get_update_homework_use_case(
        self,
        homework_repo: HomeworkRepository,
    ) -> UpdateHomeworkUseCase:
        return UpdateHomeworkUseCase(
            homework_repo=homework_repo,
        )

    @provide
    def get_delete_homework_use_case(
        self,
        homework_repo: HomeworkRepository,
    ) -> DeleteHomeworkUseCase:
        return DeleteHomeworkUseCase(homework_repo=homework_repo)

    @provide
    def get_submission_status_use_case(
        self,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        quiz_api: QuizApiClient,
        permission_repo: PermissionRequestRepository,
    ) -> GetHomeworkSubmissionStatusUseCase:
        return GetHomeworkSubmissionStatusUseCase(
            homework_repo=homework_repo,
            user_repo=user_repo,
            quiz_api=quiz_api,
            permission_repo=permission_repo,
        )

    @provide
    def get_check_overdue_use_case(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
    ) -> CheckOverdueHomeworkUseCase:
        return CheckOverdueHomeworkUseCase(
            homework_repo=homework_repo,
            quiz_api=quiz_api,
            user_repo=user_repo,
        )

    @provide
    def get_rescan_all_use_case(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
    ) -> RescanAllHomeworksUseCase:
        return RescanAllHomeworksUseCase(
            homework_repo=homework_repo,
            quiz_api=quiz_api,
            user_repo=user_repo,
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
