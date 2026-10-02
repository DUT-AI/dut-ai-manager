from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.meeting.application import (
    CalculateCurrentCapacityUseCase,
    CheckEvaluationDeadlineJobUseCase,
    CheckInUseCase,
    CheckInWithCardUseCase,
    CheckMeetingAttendanceUseCase,
    CheckOutUseCase,
    CreateMeetingUseCase,
    DeleteMeetingUseCase,
    GetMeetingEvaluationSummaryUseCase,
    GetMeetingsUseCase,
    GetMyEvaluationResultUseCase,
    SubmitTraineeEvaluationUseCase,
    SubmitTrainerEvaluationUseCase,
    UpdateMeetingUseCase,
    UpdateParticipantStatusUseCase,
)
from app.meeting.application.event_handlers import MeetingNotificationHandler
from app.meeting.application.sse_handler import MeetingSseHandler
from app.meeting.infrastructure.repository import (
    MeetingEvaluationRepository,
    MeetingRepository,
    ParticipantRepository,
)
from app.shared.infrastructure.minio_service import MinioService
from app.shared.infrastructure.notification_service import NotificationService
from app.shared.infrastructure.tts_service import TTSService
from app.user.infrastructure.repository import UserRepository
from app.violation.infrastructure.repository import ViolationRepository


class MeetingModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_meeting_repo(self, session: Session) -> MeetingRepository:
        return MeetingRepository(session)

    @provide
    def get_participant_repo(self, session: Session) -> ParticipantRepository:
        return ParticipantRepository(session)

    @provide
    def get_meeting_evaluation_repo(
        self, session: Session
    ) -> MeetingEvaluationRepository:
        return MeetingEvaluationRepository(session)

    # Use Cases
    @provide
    def get_meetings_uc(self, repo: MeetingRepository) -> GetMeetingsUseCase:
        return GetMeetingsUseCase(repo)

    @provide
    def create_meeting_uc(
        self, repo: MeetingRepository
    ) -> CreateMeetingUseCase:
        return CreateMeetingUseCase(repo)

    @provide
    def check_in_uc(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
        minio_service: MinioService,
    ) -> CheckInUseCase:
        return CheckInUseCase(meeting_repo, participant_repo, minio_service)

    @provide
    def check_in_with_card_uc(
        self,
        user_repo: UserRepository,
        participant_repo: ParticipantRepository,
        meeting_repo: MeetingRepository,
        tts_service: TTSService,
        minio_service: MinioService,
    ) -> CheckInWithCardUseCase:
        return CheckInWithCardUseCase(
            user_repo,
            participant_repo,
            meeting_repo,
            tts_service,
            minio_service,
        )

    @provide
    def check_out_uc(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
    ) -> CheckOutUseCase:
        return CheckOutUseCase(meeting_repo, participant_repo)

    @provide
    def update_meeting_uc(
        self, repo: MeetingRepository
    ) -> UpdateMeetingUseCase:
        return UpdateMeetingUseCase(repo)

    @provide
    def update_participant_status_uc(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
    ) -> UpdateParticipantStatusUseCase:
        return UpdateParticipantStatusUseCase(meeting_repo, participant_repo)

    @provide
    def delete_meeting_uc(self, repo: MeetingRepository) -> DeleteMeetingUseCase:
        return DeleteMeetingUseCase(repo)

    @provide
    def check_meeting_attendance_uc(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
    ) -> CheckMeetingAttendanceUseCase:
        return CheckMeetingAttendanceUseCase(meeting_repo, participant_repo)

    @provide
    def calculate_current_capacity_uc(
        self,
        meeting_repo: MeetingRepository,
    ) -> CalculateCurrentCapacityUseCase:
        return CalculateCurrentCapacityUseCase(meeting_repo)

    @provide
    def submit_trainer_evaluation_uc(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
    ) -> SubmitTrainerEvaluationUseCase:
        return SubmitTrainerEvaluationUseCase(meeting_repo, evaluation_repo)

    @provide
    def submit_trainee_evaluation_uc(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
    ) -> SubmitTraineeEvaluationUseCase:
        return SubmitTraineeEvaluationUseCase(meeting_repo, evaluation_repo)

    @provide
    def get_my_evaluation_result_uc(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
    ) -> GetMyEvaluationResultUseCase:
        return GetMyEvaluationResultUseCase(meeting_repo, evaluation_repo)

    @provide
    def get_meeting_evaluation_summary_uc(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
    ) -> GetMeetingEvaluationSummaryUseCase:
        return GetMeetingEvaluationSummaryUseCase(meeting_repo, evaluation_repo)

    @provide
    def check_evaluation_deadline_job_uc(
        self,
        meeting_repo: MeetingRepository,
        evaluation_repo: MeetingEvaluationRepository,
        violation_repo: ViolationRepository,
    ) -> CheckEvaluationDeadlineJobUseCase:
        return CheckEvaluationDeadlineJobUseCase(
            meeting_repo, evaluation_repo, violation_repo
        )

    @provide
    def get_meeting_notification_handler(
        self,
        notification_service: NotificationService,
        user_repo: UserRepository,
    ) -> MeetingNotificationHandler:
        return MeetingNotificationHandler(notification_service, user_repo)

    @provide
    def get_meeting_sse_handler(self) -> MeetingSseHandler:
        return MeetingSseHandler()
