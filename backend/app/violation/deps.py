"""
Violation Dependency Injection — FastAPI Depends factories.

Provides Use Case instances to controller endpoints.
"""

from typing import Annotated

from app.shared.infrastructure.database import get_session
from app.violation.application.use_cases import (CreateViolationUseCase,
                                                 DeleteViolationUseCase,
                                                 GetViolationsUseCase,
                                                 RestoreViolationUseCase,
                                                 UpdateViolationUseCase)
from app.violation.infrastructure.repository import ViolationRepository
from fastapi import Depends
from sqlmodel import Session


def _get_repo(
    session: Annotated[Session, Depends(get_session)],
) -> ViolationRepository:
    return ViolationRepository(session)


def get_create_violation_uc(
    repo: Annotated[ViolationRepository, Depends(_get_repo)],
) -> CreateViolationUseCase:
    return CreateViolationUseCase(repo)


def get_violations_uc(
    repo: Annotated[ViolationRepository, Depends(_get_repo)],
) -> GetViolationsUseCase:
    return GetViolationsUseCase(repo)


def get_update_violation_uc(
    repo: Annotated[ViolationRepository, Depends(_get_repo)],
) -> UpdateViolationUseCase:
    return UpdateViolationUseCase(repo)


def get_delete_violation_uc(
    repo: Annotated[ViolationRepository, Depends(_get_repo)],
) -> DeleteViolationUseCase:
    return DeleteViolationUseCase(repo)


def get_restore_violation_uc(
    repo: Annotated[ViolationRepository, Depends(_get_repo)],
) -> RestoreViolationUseCase:
    return RestoreViolationUseCase(repo)
