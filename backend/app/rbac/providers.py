from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.rbac.application.use_cases import RoleApiKeyUseCases, RoleUseCases
from app.rbac.infrastructure.repository import (
    PermissionRepository,
    RoleApiKeyRepository,
    RolePermissionRepository,
    RoleRepository,
)


class RbacModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_role_repo(self, session: Session) -> RoleRepository:
        return RoleRepository(session)

    @provide
    def get_permission_repo(self, session: Session) -> PermissionRepository:
        return PermissionRepository(session)

    @provide
    def get_role_permission_repo(self, session: Session) -> RolePermissionRepository:
        return RolePermissionRepository(session)

    @provide
    def get_role_api_key_repo(self, session: Session) -> RoleApiKeyRepository:
        return RoleApiKeyRepository(session)

    @provide
    def get_role_use_cases(
        self,
        role_repo: RoleRepository,
        permission_repo: PermissionRepository,
        role_permission_repo: RolePermissionRepository,
    ) -> RoleUseCases:
        return RoleUseCases(
            role_repo=role_repo,
            permission_repo=permission_repo,
            role_permission_repo=role_permission_repo,
        )

    @provide
    def get_role_api_key_use_cases(
        self,
        api_key_repo: RoleApiKeyRepository,
        role_repo: RoleRepository,
    ) -> RoleApiKeyUseCases:
        return RoleApiKeyUseCases(api_key_repo=api_key_repo, role_repo=role_repo)
