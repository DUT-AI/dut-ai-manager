from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.homework.application import (
    CheckOverdueHomeworkUseCase,
    CreateHomeworkUseCase,
    DeleteHomeworkUseCase,
    GetHomeworkSubmissionStatusUseCase,
    GetHomeworksUseCase,
    GetUserHomeworkSubmissionsUseCase,
    RecordHomeworkSubmissionUseCase,
    RescanAllHomeworksUseCase,
    SyncHomeworkFromQuizUseCase,
    UpdateHomeworkUseCase,
)
from app.homework.application.event_handlers import (
    HomeworkGradedNotificationHandler,
    HomeworkNotificationHandler,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.homework.infrastructure.repository import (
    HomeworkRepository,
)
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.infrastructure.notification_service import NotificationService
from app.user.infrastructure.repository import UserRepository


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
        quiz_api: QuizApiClient,
    ) -> CreateHomeworkUseCase:
        return CreateHomeworkUseCase(
            homework_repo=homework_repo,
            quiz_api=quiz_api,
        )

    @provide
    def get_update_homework_use_case(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
    ) -> UpdateHomeworkUseCase:
        return UpdateHomeworkUseCase(
            homework_repo=homework_repo,
            quiz_api=quiz_api,
        )

    @provide
    def get_delete_homework_use_case(
        self,
        homework_repo: HomeworkRepository,
    ) -> DeleteHomeworkUseCase:
        return DeleteHomeworkUseCase(homework_repo=homework_repo)

    @provide
    def get_record_submission_use_case(
        self,
        homework_repo: HomeworkRepository,
    ) -> RecordHomeworkSubmissionUseCase:
        return RecordHomeworkSubmissionUseCase(homework_repo=homework_repo)

    @provide
    def get_user_submissions_use_case(
        self,
        homework_repo: HomeworkRepository,
    ) -> GetUserHomeworkSubmissionsUseCase:
        return GetUserHomeworkSubmissionsUseCase(homework_repo=homework_repo)

    @provide
    def get_sync_homework_use_case(
        self,
        homework_repo: HomeworkRepository,
        quiz_api: QuizApiClient,
    ) -> SyncHomeworkFromQuizUseCase:
        return SyncHomeworkFromQuizUseCase(
            homework_repo=homework_repo,
            quiz_api=quiz_api,
        )

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
        notification_service: NotificationService,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
    ) -> HomeworkNotificationHandler:
        return HomeworkNotificationHandler(
            notification_service, homework_repo, user_repo
        )

    @provide
    def get_graded_notification_handler(
        self,
        notification_service: NotificationService,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
    ) -> HomeworkGradedNotificationHandler:
        return HomeworkGradedNotificationHandler(
            notification_service, homework_repo, user_repo
        )
