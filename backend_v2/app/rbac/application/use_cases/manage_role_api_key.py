from app.rbac.application.dtos import RoleApiKeyResponse
from app.rbac.domain.exceptions import (RoleApiKeyNotFoundException,
                                        RoleNotFoundException)
from app.rbac.domain.interfaces import IRoleApiKeyRepository, IRoleRepository


class GetRoleApiKeysUseCase:
    def __init__(self, key_repo: IRoleApiKeyRepository, role_repo: IRoleRepository):
        self.key_repo = key_repo
        self.role_repo = role_repo

    async def execute(self, role_id: int) -> list[RoleApiKeyResponse]:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFoundException(role_id)

        keys = await self.key_repo.get_by_role_id(role_id)
        return [RoleApiKeyResponse.model_validate(k) for k in keys]


class RevokeRoleApiKeyUseCase:
    def __init__(self, key_repo: IRoleApiKeyRepository):
        self.key_repo = key_repo

    async def execute(self, key_id: int) -> None:
        existing_key = await self.key_repo.get_by_id(key_id)
        if not existing_key:
            raise RoleApiKeyNotFoundException(key_id)

        await self.key_repo.delete(key_id)
