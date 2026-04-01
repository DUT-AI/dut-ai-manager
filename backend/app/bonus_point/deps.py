"""
Bonus Point Dependency Injection — FastAPI Depends factories.

Provides Use Case instances to controller endpoints.
"""

from typing import Annotated

from app.bonus_point.application.use_cases import (CreateBonusPointsUseCase,
                                                   DeleteBonusPointUseCase,
                                                   GetBonusPointsUseCase,
                                                   RestoreBonusPointUseCase,
                                                   UpdateBonusPointUseCase)
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.shared.infrastructure.database import get_session
from fastapi import Depends
from sqlmodel import Session


def _get_repo(
    session: Annotated[Session, Depends(get_session)],
) -> BonusPointRepository:
    return BonusPointRepository(session)


def get_create_bonus_points_uc(
    repo: Annotated[BonusPointRepository, Depends(_get_repo)],
) -> CreateBonusPointsUseCase:
    return CreateBonusPointsUseCase(repo)


def get_bonus_points_uc(
    repo: Annotated[BonusPointRepository, Depends(_get_repo)],
) -> GetBonusPointsUseCase:
    return GetBonusPointsUseCase(repo)


def get_update_bonus_point_uc(
    repo: Annotated[BonusPointRepository, Depends(_get_repo)],
) -> UpdateBonusPointUseCase:
    return UpdateBonusPointUseCase(repo)


def get_delete_bonus_point_uc(
    repo: Annotated[BonusPointRepository, Depends(_get_repo)],
) -> DeleteBonusPointUseCase:
    return DeleteBonusPointUseCase(repo)


def get_restore_bonus_point_uc(
    repo: Annotated[BonusPointRepository, Depends(_get_repo)],
) -> RestoreBonusPointUseCase:
    return RestoreBonusPointUseCase(repo)
