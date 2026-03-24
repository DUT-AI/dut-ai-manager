from app.rbac.application.use_cases.create_role_api_key import \
  CreateRoleApiKeyUseCase
from app.rbac.application.use_cases.get_roles import (GetRoleByIdUseCase,
                                                      GetRolesUseCase)
from app.rbac.application.use_cases.manage_permission import (
  CreatePermissionUseCase, DeletePermissionUseCase, GetPermissionsUseCase)
from app.rbac.application.use_cases.manage_role import (CreateRoleUseCase,
                                                        DeleteRoleUseCase,
                                                        UpdateRoleUseCase)
from app.rbac.application.use_cases.manage_role_api_key import (
  GetRoleApiKeysUseCase, RevokeRoleApiKeyUseCase)
from app.rbac.application.use_cases.manage_role_permission import (
  AssignPermissionToRoleUseCase, RemovePermissionFromRoleUseCase)
from app.rbac.domain.interfaces import (IPermissionRepository,
                                        IRoleApiKeyRepository, IRoleRepository)
from app.rbac.infrastructure.repositories import (
  SQLAlchemyPermissionRepository, SQLAlchemyRoleApiKeyRepository,
  SQLAlchemyRoleRepository)
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession


class RbacProvider(Provider):
    # Repositories (Request scope because they depend on AsyncSession)
    @provide(scope=Scope.REQUEST)
    def role_repository(self, session: AsyncSession) -> IRoleRepository:
        return SQLAlchemyRoleRepository(session)

    @provide(scope=Scope.REQUEST)
    def permission_repository(self, session: AsyncSession) -> IPermissionRepository:
        return SQLAlchemyPermissionRepository(session)

    @provide(scope=Scope.REQUEST)
    def role_api_key_repository(self, session: AsyncSession) -> IRoleApiKeyRepository:
        return SQLAlchemyRoleApiKeyRepository(session)

    # Use Cases - Role (Request scope)
    @provide(scope=Scope.REQUEST)
    def get_roles_use_case(self, repo: IRoleRepository) -> GetRolesUseCase:
        return GetRolesUseCase(repo)

    @provide(scope=Scope.REQUEST)
    def get_role_by_id_use_case(self, repo: IRoleRepository) -> GetRoleByIdUseCase:
        return GetRoleByIdUseCase(repo)

    @provide(scope=Scope.REQUEST)
    def create_role_use_case(self, repo: IRoleRepository) -> CreateRoleUseCase:
        return CreateRoleUseCase(repo)

    @provide(scope=Scope.REQUEST)
    def update_role_use_case(self, repo: IRoleRepository) -> UpdateRoleUseCase:
        return UpdateRoleUseCase(repo)

    @provide(scope=Scope.REQUEST)
    def delete_role_use_case(self, repo: IRoleRepository) -> DeleteRoleUseCase:
        return DeleteRoleUseCase(repo)

    # Use Cases - Permission (Request scope)
    @provide(scope=Scope.REQUEST)
    def get_permissions_use_case(
        self, repo: IPermissionRepository
    ) -> GetPermissionsUseCase:
        return GetPermissionsUseCase(repo)

    @provide(scope=Scope.REQUEST)
    def create_permission_use_case(
        self, repo: IPermissionRepository
    ) -> CreatePermissionUseCase:
        return CreatePermissionUseCase(repo)

    @provide(scope=Scope.REQUEST)
    def delete_permission_use_case(
        self, repo: IPermissionRepository
    ) -> DeletePermissionUseCase:
        return DeletePermissionUseCase(repo)

    # Use Cases - Role-Permission Link (Request scope)
    @provide(scope=Scope.REQUEST)
    def assign_permission_to_role_use_case(
        self, role_repo: IRoleRepository, perm_repo: IPermissionRepository
    ) -> AssignPermissionToRoleUseCase:
        return AssignPermissionToRoleUseCase(role_repo, perm_repo)

    @provide(scope=Scope.REQUEST)
    def remove_permission_from_role_use_case(
        self, role_repo: IRoleRepository, perm_repo: IPermissionRepository
    ) -> RemovePermissionFromRoleUseCase:
        return RemovePermissionFromRoleUseCase(role_repo, perm_repo)

    # Use Cases - API Key (Request scope)
    @provide(scope=Scope.REQUEST)
    def create_role_api_key_use_case(
        self, role_repo: IRoleRepository, key_repo: IRoleApiKeyRepository
    ) -> CreateRoleApiKeyUseCase:
        return CreateRoleApiKeyUseCase(role_repo, key_repo)

    @provide(scope=Scope.REQUEST)
    def get_role_api_keys_use_case(
        self, key_repo: IRoleApiKeyRepository, role_repo: IRoleRepository
    ) -> GetRoleApiKeysUseCase:
        return GetRoleApiKeysUseCase(key_repo, role_repo)

    @provide(scope=Scope.REQUEST)
    def revoke_role_api_key_use_case(
        self, key_repo: IRoleApiKeyRepository
    ) -> RevokeRoleApiKeyUseCase:
        return RevokeRoleApiKeyUseCase(key_repo)
