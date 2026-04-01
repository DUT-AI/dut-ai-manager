from app.core.database import get_session
from app.homework.application.use_cases import HomeworkUseCases
from app.homework.infrastructure.repository import (
  HomeworkRepository, HomeworkSubmissionRepository)
from app.shared.infrastructure.minio_service import MinioService
from app.team.deps import get_team_repository
from app.team.infrastructure.repository import TeamRepository
from app.user.deps import get_user_repo
from app.user.infrastructure.repository import UserRepository
from fastapi import Depends
from sqlmodel import Session


def get_homework_repo(session: Session = Depends(get_session)) -> HomeworkRepository:
    return HomeworkRepository(session)


def get_submission_repo(
    session: Session = Depends(get_session),
) -> HomeworkSubmissionRepository:
    return HomeworkSubmissionRepository(session)


def get_homework_use_cases(
    homework_repo: HomeworkRepository = Depends(get_homework_repo),
    submission_repo: HomeworkSubmissionRepository = Depends(get_submission_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    team_repo: TeamRepository = Depends(get_team_repository),
) -> HomeworkUseCases:
    minio_service = MinioService()

    return HomeworkUseCases(
        homework_repo=homework_repo,
        submission_repo=submission_repo,
        user_repo=user_repo,
        team_repo=team_repo,
        minio_service=minio_service,
    )
