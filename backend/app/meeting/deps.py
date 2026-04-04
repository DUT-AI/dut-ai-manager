from typing import Annotated

from app.meeting.application.use_cases import (
    CheckInUseCase,
    CheckInWithCardUseCase,
    CreateMeetingUseCase,
    DeleteMeetingUseCase,
    GetMeetingsUseCase,
    UpdateMeetingUseCase,
)
from app.meeting.infrastructure.repository import (
    MeetingRepository,
    ParticipantRepository,
)
from app.team.infrastructure.repository import TeamRepository
from app.shared.infrastructure.database import get_session
from app.user.infrastructure.repository import UserRepository
from app.shared.infrastructure.minio_service import MinioService
from app.user.deps import get_minio_service
from fastapi import Depends
from sqlmodel import Session


def _get_meeting_repo(
    session: Annotated[Session, Depends(get_session)],
) -> MeetingRepository:
    return MeetingRepository(session)


def _get_participant_repo(
    session: Annotated[Session, Depends(get_session)],
) -> ParticipantRepository:
    return ParticipantRepository(session)


def _get_user_repo(
    session: Annotated[Session, Depends(get_session)],
) -> UserRepository:
    return UserRepository(session)


def _get_team_repo(
    session: Annotated[Session, Depends(get_session)],
) -> TeamRepository:
    return TeamRepository(session)


def get_meetings_uc(
    repo: Annotated[MeetingRepository, Depends(_get_meeting_repo)],
) -> GetMeetingsUseCase:
    return GetMeetingsUseCase(repo)


def get_create_meeting_uc(
    repo: Annotated[MeetingRepository, Depends(_get_meeting_repo)],
    team_repo: Annotated[TeamRepository, Depends(_get_team_repo)],
) -> CreateMeetingUseCase:
    return CreateMeetingUseCase(repo, team_repo)


def get_update_meeting_uc(
    repo: Annotated[MeetingRepository, Depends(_get_meeting_repo)],
    team_repo: Annotated[TeamRepository, Depends(_get_team_repo)],
) -> UpdateMeetingUseCase:
    return UpdateMeetingUseCase(repo, team_repo)


def get_delete_meeting_uc(
    repo: Annotated[MeetingRepository, Depends(_get_meeting_repo)],
) -> DeleteMeetingUseCase:
    return DeleteMeetingUseCase(repo)


def get_check_in_uc(
    meeting_repo: Annotated[MeetingRepository, Depends(_get_meeting_repo)],
    participant_repo: Annotated[ParticipantRepository, Depends(_get_participant_repo)],
    minio_service: Annotated[MinioService, Depends(get_minio_service)],
) -> CheckInUseCase:
    return CheckInUseCase(meeting_repo, participant_repo, minio_service)


def get_check_in_with_card_uc(
    user_repo: Annotated[UserRepository, Depends(_get_user_repo)],
    participant_repo: Annotated[ParticipantRepository, Depends(_get_participant_repo)],
    meeting_repo: Annotated[MeetingRepository, Depends(_get_meeting_repo)],
) -> CheckInWithCardUseCase:
    return CheckInWithCardUseCase(user_repo, participant_repo, meeting_repo)
