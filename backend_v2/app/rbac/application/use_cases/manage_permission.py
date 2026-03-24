from app.rbac.application.dtos import (PermissionCreate, PermissionResponse,
                                       PermissionUpdate)
from app.rbac.domain.entities import Permission
from app.rbac.domain.exceptions import (PermissionAlreadyExistsException,
                                        PermissionNotFoundException)
from app.rbac.domain.interfaces import IPermissionRepository


class CreatePermissionUseCase:
    def __init__(self, permission_repo: IPermissionRepository):
        self.permission_repo = permission_repo

    async def execute(self, dto: PermissionCreate) -> PermissionResponse:
        existing = await self.permission_repo.get_by_name(dto.name)
        if existing:
            raise PermissionAlreadyExistsException(dto.name)

        permission = Permission(
            id=0,
            name=dto.name,
            description=dto.description,
            resource=dto.resource,
            action=dto.action,
        )
        saved = await self.permission_repo.create(permission)
        return PermissionResponse.model_validate(saved)


class GetPermissionsUseCase:
    def __init__(self, permission_repo: IPermissionRepository):
        self.permission_repo = permission_repo

    async def execute(self) -> list[PermissionResponse]:
        perms = await self.permission_repo.get_all()
        return [PermissionResponse.model_validate(p) for p in perms]


class DeletePermissionUseCase:
    def __init__(self, permission_repo: IPermissionRepository):
        self.permission_repo = permission_repo

    async def execute(self, permission_id: int) -> None:
        perm = await self.permission_repo.get_by_id(permission_id)
        if not perm:
            raise PermissionNotFoundException(permission_id)

        await self.permission_repo.delete(permission_id)
