from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.rbac.application.use_cases import RoleApiKeyUseCases, RoleUseCases
from app.rbac.infrastructure.repository import (
    PermissionRepository,
    RoleApiKeyRepository,
    RolePermissionRepository,
    RoleRepository,
)
from app.shared.infrastructure.database import get_session


def get_role_repository(session: Session = Depends(get_session)) -> RoleRepository:
    return RoleRepository(session)


def get_permission_repository(
    session: Session = Depends(get_session),
) -> PermissionRepository:
    return PermissionRepository(session)


def get_role_permission_repository(
    session: Session = Depends(get_session),
) -> RolePermissionRepository:
    return RolePermissionRepository(session)


def get_role_api_key_repository(
    session: Session = Depends(get_session),
) -> RoleApiKeyRepository:
    return RoleApiKeyRepository(session)


def get_role_use_cases(
    role_repo: RoleRepository = Depends(get_role_repository),
    permission_repo: PermissionRepository = Depends(get_permission_repository),
    role_permission_repo: RolePermissionRepository = Depends(
        get_role_permission_repository
    ),
) -> RoleUseCases:
    return RoleUseCases(
        role_repo=role_repo,
        permission_repo=permission_repo,
        role_permission_repo=role_permission_repo,
    )


def get_role_api_key_use_cases(
    api_key_repo: RoleApiKeyRepository = Depends(get_role_api_key_repository),
    role_repo: RoleRepository = Depends(get_role_repository),
) -> RoleApiKeyUseCases:
    return RoleApiKeyUseCases(api_key_repo=api_key_repo, role_repo=role_repo)


RoleUseCasesDI = Annotated[RoleUseCases, Depends(get_role_use_cases)]
RoleApiKeyUseCasesDI = Annotated[
    RoleApiKeyUseCases, Depends(get_role_api_key_use_cases)
]
