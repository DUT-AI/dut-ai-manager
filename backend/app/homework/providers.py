from dishka import Provider, Scope, alias, provide
from sqlalchemy.orm import Session

from app.homework.application import (
    CheckOverdueHomeworkUseCase,
    CreateHomeworkUseCase,
    DeleteHomeworkUseCase,
    GetHomeworkDetailUseCase,
    GetHomeworksPagedUseCase,
    GetHomeworkSubmissionStatusUseCase,
    GetUnsubmittedHomeworkReportUseCase,
    GetUnsubmittedHomeworksForUserUseCase,
    GetUserHomeworkSubmissionsUseCase,
    GetUserHomeworksUseCase,
    HomeworkExerciseResolver,
    RecordHomeworkSubmissionUseCase,
    RescanAllHomeworksUseCase,
    SyncHomeworkFromQuizUseCase,
    UpdateHomeworkUseCase,
)
from app.homework.application.event_handlers import (
    HomeworkGradedNotificationHandler,
    HomeworkNotificationHandler,
)
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkRepositoryPort,
    HomeworkSubmissionRepositoryPort,
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
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.user.infrastructure.repository import UserRepository


class HomeworkModuleProvider(Provider):
    scope = Scope.REQUEST

    homework_repo_port = alias(
        source=HomeworkRepository, provides=HomeworkRepositoryPort
    )
    homework_submission_repo_port = alias(
        source=HomeworkSubmissionRepository,
        provides=HomeworkSubmissionRepositoryPort,
    )
    homework_assignee_repo_port = alias(
        source=HomeworkAssigneeRepository,
        provides=HomeworkAssigneeRepositoryPort,
    )

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
        homework_assignee_repo: HomeworkAssigneeRepository,
    ) -> GetHomeworksPagedUseCase:
        return GetHomeworksPagedUseCase(
            homework_repo=homework_repo,
            homework_assignee_repo=homework_assignee_repo,
        )

    @provide
    def get_homework_exercise_resolver(
        self,
        quiz_api: QuizApiClient,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
    ) -> HomeworkExerciseResolver:
        return HomeworkExerciseResolver(
            quiz_api=quiz_api,
            homework_submission_repo=homework_submission_repo,
        )

    @provide
    def get_get_homework_detail_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        exercise_resolver: HomeworkExerciseResolver,
    ) -> GetHomeworkDetailUseCase:
        return GetHomeworkDetailUseCase(
            homework_repo=homework_repo,
            homework_assignee_repo=homework_assignee_repo,
            exercise_resolver=exercise_resolver,
        )

    @provide
    def get_get_user_homeworks_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
    ) -> GetUserHomeworksUseCase:
        return GetUserHomeworksUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
        )

    @provide
    def get_get_unsubmitted_homeworks_for_user_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
    ) -> GetUnsubmittedHomeworksForUserUseCase:
        return GetUnsubmittedHomeworksForUserUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
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
            user_repo=user_repo,
            homework_assignee_repo=homework_assignee_repo,
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
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
    ) -> RecordHomeworkSubmissionUseCase:
        return RecordHomeworkSubmissionUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
        )

    @provide
    def get_user_submissions_use_case(
        self,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
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
        exercise_resolver: HomeworkExerciseResolver,
    ) -> GetHomeworkSubmissionStatusUseCase:
        return GetHomeworkSubmissionStatusUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
            user_repo=user_repo,
            exercise_resolver=exercise_resolver,
        )

    @provide
    def get_check_overdue_use_case(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_submission_repo: HomeworkSubmissionRepositoryPort,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        exercise_resolver: HomeworkExerciseResolver,
    ) -> CheckOverdueHomeworkUseCase:
        return CheckOverdueHomeworkUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
            exercise_resolver=exercise_resolver,
        )

    @provide
    def get_rescan_all_use_case(
        self,
        homework_repo: HomeworkRepository,
        homework_submission_repo: HomeworkSubmissionRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        exercise_resolver: HomeworkExerciseResolver,
        user_repo: UserRepository,
    ) -> RescanAllHomeworksUseCase:
        return RescanAllHomeworksUseCase(
            homework_repo=homework_repo,
            homework_submission_repo=homework_submission_repo,
            homework_assignee_repo=homework_assignee_repo,
            exercise_resolver=exercise_resolver,
            user_repo=user_repo,
        )

    @provide
    def get_notification_handler(
        self,
        dispatcher: UnifiedNotificationDispatcher,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
    ) -> HomeworkNotificationHandler:
        return HomeworkNotificationHandler(
            dispatcher, homework_repo, user_repo, homework_assignee_repo
        )

    @provide
    def get_graded_notification_handler(
        self,
        dispatcher: UnifiedNotificationDispatcher,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
    ) -> HomeworkGradedNotificationHandler:
        return HomeworkGradedNotificationHandler(dispatcher, homework_repo, user_repo)
