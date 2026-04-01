from app.core.database import get_session
from app.team.application.use_cases import TeamUseCases
from app.team.infrastructure.repository import TeamRepository
from fastapi import Depends
from sqlmodel import Session


def get_team_repository(session: Session = Depends(get_session)) -> TeamRepository:
    return TeamRepository(session)


def get_team_usecases(
    repo: TeamRepository = Depends(get_team_repository),
) -> TeamUseCases:
    return TeamUseCases(repo)
