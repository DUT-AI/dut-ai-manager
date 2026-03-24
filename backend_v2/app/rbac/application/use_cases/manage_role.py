from app.rbac.application.dtos import RoleCreate, RoleResponse, RoleUpdate
from app.rbac.domain.entities import Role
from app.rbac.domain.exceptions import (RoleAlreadyExistsException,
                                        RoleNotFoundException)
from app.rbac.domain.interfaces import IRoleRepository


class CreateRoleUseCase:
    def __init__(self, role_repo: IRoleRepository):
        self.role_repo = role_repo

    async def execute(self, dto: RoleCreate) -> RoleResponse:
        existing_role = await self.role_repo.get_by_name(dto.name)
        if existing_role:
            raise RoleAlreadyExistsException(dto.name)

        role = Role(
            id=0,
            name=dto.name,
            description=dto.description,
            permissions=[],
        )
        saved_role = await self.role_repo.create(role)
        return RoleResponse.model_validate(saved_role)


class UpdateRoleUseCase:
    def __init__(self, role_repo: IRoleRepository):
        self.role_repo = role_repo

    async def execute(self, role_id: int, dto: RoleUpdate) -> RoleResponse:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFoundException(role_id)

        if dto.name and dto.name != role.name:
            existing_role = await self.role_repo.get_by_name(dto.name)
            if existing_role:
                raise RoleAlreadyExistsException(dto.name)
            role.name = dto.name

        if dto.description is not None:
            role.description = dto.description

        updated_role = await self.role_repo.update(role)
        return RoleResponse.model_validate(updated_role)


class DeleteRoleUseCase:
    def __init__(self, role_repo: IRoleRepository):
        self.role_repo = role_repo

    async def execute(self, role_id: int) -> None:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFoundException(role_id)

        await self.role_repo.delete(role_id)
