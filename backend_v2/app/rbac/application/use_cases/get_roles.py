from app.rbac.application.dtos import RoleResponse
from app.rbac.domain.exceptions import RoleNotFoundException
from app.rbac.domain.interfaces import IRoleRepository


class GetRolesUseCase:
    def __init__(self, role_repo: IRoleRepository):
        self.role_repo = role_repo

    async def execute(self) -> list[RoleResponse]:
        roles = await self.role_repo.get_all()
        return [RoleResponse.model_validate(role) for role in roles]


class GetRoleByIdUseCase:
    def __init__(self, role_repo: IRoleRepository):
        self.role_repo = role_repo

    async def execute(self, role_id: int) -> RoleResponse:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFoundException(role_id)
        return RoleResponse.model_validate(role)
