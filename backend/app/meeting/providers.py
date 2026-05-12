from dishka import Provider, Scope, provide
from sqlmodel import Session
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.meeting.application.use_cases import (
    GetMeetingsUseCase,
    CreateMeetingUseCase,
    CheckInUseCase,
    CheckInWithCardUseCase,
    CheckOutUseCase,
    UpdateMeetingUseCase,
    DeleteMeetingUseCase,
    MeetingUseCases,
    CheckMeetingAttendanceUseCase,
)
from app.meeting.application.capacity_use_cases import CalculateCurrentCapacityUseCase
from app.meeting.application.event_handlers import MeetingNotificationHandler
from app.meeting.application.sse_handler import MeetingSseHandler
from app.user.infrastructure.repository import UserRepository
from app.team.infrastructure.repository import TeamRepository
from app.shared.infrastructure.minio_service import MinioService
from app.shared.infrastructure.discord_service import DiscordService
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient
from app.permission_request.infrastructure.repository import PermissionRequestRepository


class MeetingModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_meeting_repo(self, session: Session) -> MeetingRepository:
        return MeetingRepository(session)

    @provide
    def get_participant_repo(self, session: Session) -> ParticipantRepository:
        return ParticipantRepository(session)

    # Use Cases
    @provide
    def get_meetings_uc(self, repo: MeetingRepository) -> GetMeetingsUseCase:
        return GetMeetingsUseCase(repo)

    @provide
    def create_meeting_uc(
        self, repo: MeetingRepository, team_repo: TeamRepository
    ) -> CreateMeetingUseCase:
        return CreateMeetingUseCase(repo, team_repo)

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
    ) -> CheckInWithCardUseCase:
        return CheckInWithCardUseCase(user_repo, participant_repo, meeting_repo)

    @provide
    def check_out_uc(
        self,
        meeting_repo: MeetingRepository,
        participant_repo: ParticipantRepository,
    ) -> CheckOutUseCase:
        return CheckOutUseCase(meeting_repo, participant_repo)

    @provide
    def update_meeting_uc(
        self, repo: MeetingRepository, team_repo: TeamRepository
    ) -> UpdateMeetingUseCase:
        return UpdateMeetingUseCase(repo, team_repo)

    @provide
    def delete_meeting_uc(self, repo: MeetingRepository) -> DeleteMeetingUseCase:
        return DeleteMeetingUseCase(repo)

    @provide
    def check_meeting_attendance_uc(
        self,
        meeting_repo: MeetingRepository,
        permission_repo: PermissionRequestRepository,
    ) -> CheckMeetingAttendanceUseCase:
        return CheckMeetingAttendanceUseCase(meeting_repo, permission_repo)

    @provide
    def calculate_current_capacity_uc(
        self,
        meeting_repo: MeetingRepository,
    ) -> CalculateCurrentCapacityUseCase:
        return CalculateCurrentCapacityUseCase(meeting_repo)

    @provide
    def meeting_use_cases(
        self,
        get_meetings: GetMeetingsUseCase,
        create_meeting: CreateMeetingUseCase,
        update_meeting: UpdateMeetingUseCase,
        delete_meeting: DeleteMeetingUseCase,
        check_in: CheckInUseCase,
        repo: MeetingRepository,
    ) -> MeetingUseCases:
        return MeetingUseCases(
            get_meetings, create_meeting, update_meeting, delete_meeting, check_in, repo
        )

    @provide
    def get_meeting_notification_handler(
        self,
        discord_service: DiscordService,
        user_repo: UserRepository,
        zalo_bot: ZaloBotClient,
    ) -> MeetingNotificationHandler:
        return MeetingNotificationHandler(discord_service, user_repo, zalo_bot)

    @provide
    def get_meeting_sse_handler(self) -> MeetingSseHandler:
        return MeetingSseHandler()
