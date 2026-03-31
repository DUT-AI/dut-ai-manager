import secrets

import bcrypt
from app.rbac.application.dtos import RoleApiKeyCreate, RoleApiKeySecret
from app.rbac.domain.entities import RoleApiKey
from app.rbac.domain.exceptions import RoleNotFoundException
from app.rbac.domain.interfaces import IRoleApiKeyRepository, IRoleRepository


class CreateRoleApiKeyUseCase:
    def __init__(
        self,
        role_repo: IRoleRepository,
        api_key_repo: IRoleApiKeyRepository,
    ):
        self.role_repo = role_repo
        self.api_key_repo = api_key_repo

    async def execute(self, role_id: int, dto: RoleApiKeyCreate) -> RoleApiKeySecret:
        # Check if role exists
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFoundException(role_id)

        # Generate API key
        raw_key = f"sk-{secrets.token_urlsafe(32)}"
        prefix = raw_key[:10]
        hashed_key = bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

        api_key_entity = RoleApiKey(
            id=0,  # Will be set by DB
            name=dto.name,
            key_hash=hashed_key,
            prefix=prefix,
            is_active=True,
            role_id=role_id,
        )

        saved_api_key = await self.api_key_repo.create(api_key_entity)
        assert saved_api_key.id is not None, "API key ID must be set after save"

        # Build response with the raw key (only returned here)
        return RoleApiKeySecret(
            id=saved_api_key.id,
            name=saved_api_key.name,
            prefix=saved_api_key.prefix,
            is_active=saved_api_key.is_active,
            role_id=saved_api_key.role_id,
            key=raw_key,
        )
