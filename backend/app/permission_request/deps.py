from typing import Annotated

from app.permission_request.application.use_cases import (
  CreatePermissionRequestUseCase, DeletePermissionRequestUseCase,
  GetPermissionRequestsUseCase, RestorePermissionRequestUseCase,
  UpdatePermissionRequestUseCase)
from app.permission_request.infrastructure.repository import \
  PermissionRequestRepository
from app.shared.infrastructure.database import get_session
from fastapi import Depends
from sqlmodel import Session


def _get_permission_repo(
    session: Annotated[Session, Depends(get_session)],
) -> PermissionRequestRepository:
    return PermissionRequestRepository(session)


def get_requests_uc(
    repo: Annotated[PermissionRequestRepository, Depends(_get_permission_repo)],
) -> GetPermissionRequestsUseCase:
    return GetPermissionRequestsUseCase(repo)


def get_create_request_uc(
    repo: Annotated[PermissionRequestRepository, Depends(_get_permission_repo)],
) -> CreatePermissionRequestUseCase:
    return CreatePermissionRequestUseCase(repo)


def get_update_request_uc(
    repo: Annotated[PermissionRequestRepository, Depends(_get_permission_repo)],
) -> UpdatePermissionRequestUseCase:
    return UpdatePermissionRequestUseCase(repo)


def get_delete_request_uc(
    repo: Annotated[PermissionRequestRepository, Depends(_get_permission_repo)],
) -> DeletePermissionRequestUseCase:
    return DeletePermissionRequestUseCase(repo)


def get_restore_request_uc(
    repo: Annotated[PermissionRequestRepository, Depends(_get_permission_repo)],
) -> RestorePermissionRequestUseCase:
    return RestorePermissionRequestUseCase(repo)
