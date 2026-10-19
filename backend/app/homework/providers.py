from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.homework.application import (
    CheckOverdueHomeworkUseCase,
    CreateHomeworkUseCase,
    DeleteHomeworkUseCase,
    GetHomeworkDetailUseCase,
    GetHomeworkSubmissionStatusUseCase,
    GetHomeworksPagedUseCase,
    GetUnsubmittedHomeworkReportUseCase,
    GetUnsubmittedHomeworksForUserUseCase,
    GetUserHomeworkSubmissionsUseCase,
    GetUserHomeworksUseCase,
    RecordHomeworkSubmissionUseCase,
    RescanAllHomeworksUseCase,
    SyncHomeworkFromQuizUseCase,
    UpdateHomeworkUseCase,
)
from app.homework.application.event_handlers import (
    HomeworkGradedNotificationHandler,
    HomeworkNotificationHandler,
)
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import (
    HomeworkRepository,
)
from app.homework.infrastructure.homework_submission_repository import (
    HomeworkSubmissionRepository,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
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
    def get_homework_submission_repo(
        self, session: Session
    ) -> HomeworkSubmissionRepository:
        return HomeworkSubmissionRepository(session)

    @provide
    def get_homework_assignee_repo(
        self, session: Session
    ) -> HomeworkAssigneeRepository:
        return HomeworkAssigneeRepository(session)

    @provide
    def get_get_homeworks_paged_use_case(
        self,
        homework_repo: HomeworkRepository,
    ) -> GetHomeworksPagedUseCase:
        return GetHomeworksPagedUseCase(homework_repo=homework_repo)

    @provide
    def get_get_homework_detail_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
    ) -> GetHomeworkDetailUseCase:
        return GetHomeworkDetailUseCase(
            homework_repo=homework_repo,
            homework_assignee_repo=homework_assignee_repo,
        )

    @provide
    def get_get_user_homeworks_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
    ) -> GetUserHomeworksUseCase:
        return GetUserHomeworksUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
        )

    @provide
    def get_get_unsubmitted_homeworks_for_user_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
    ) -> GetUnsubmittedHomeworksForUserUseCase:
        return GetUnsubmittedHomeworksForUserUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
        )

    @provide
    def get_get_unsubmitted_homework_report_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        user_repo: UserRepository,
    ) -> GetUnsubmittedHomeworkReportUseCase:
        return GetUnsubmittedHomeworkReportUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
            user_repo=user_repo,
        )

    @provide
    def get_create_homework_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        quiz_api: QuizApiClient,
    ) -> CreateHomeworkUseCase:
        return CreateHomeworkUseCase(
            homework_repo=homework_repo,
            homework_assignee_repo=homework_assignee_repo,
            quiz_api=quiz_api,
        )

    @provide
    def get_update_homework_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        quiz_api: QuizApiClient,
    ) -> UpdateHomeworkUseCase:
        return UpdateHomeworkUseCase(
            homework_repo=homework_repo,
            homework_assignee_repo=homework_assignee_repo,
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
        homework_submission_repo: HomeworkSubmissionRepository,
    ) -> RecordHomeworkSubmissionUseCase:
        return RecordHomeworkSubmissionUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
        )

    @provide
    def get_user_submissions_use_case(
        self,
        homework_submission_repo: HomeworkSubmissionRepository,
    ) -> GetUserHomeworkSubmissionsUseCase:
        return GetUserHomeworkSubmissionsUseCase(
            homework_submission_repo=homework_submission_repo
        )

    @provide
    def get_sync_homework_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        quiz_api: QuizApiClient,
    ) -> SyncHomeworkFromQuizUseCase:
        return SyncHomeworkFromQuizUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            quiz_api=quiz_api,
        )

    @provide
    def get_submission_status_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        user_repo: UserRepository,
        quiz_api: QuizApiClient,
        permission_repo: PermissionRequestRepository,
    ) -> GetHomeworkSubmissionStatusUseCase:
        return GetHomeworkSubmissionStatusUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
            user_repo=user_repo,
            quiz_api=quiz_api,
            permission_repo=permission_repo,
        )

    @provide
    def get_check_overdue_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
    ) -> CheckOverdueHomeworkUseCase:
        return CheckOverdueHomeworkUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
            quiz_api=quiz_api,
            user_repo=user_repo,
        )

    @provide
    def get_rescan_all_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        quiz_api: QuizApiClient,
        user_repo: UserRepository,
    ) -> RescanAllHomeworksUseCase:
        return RescanAllHomeworksUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
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
