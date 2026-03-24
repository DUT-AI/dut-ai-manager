from app.rbac.domain.exceptions import (PermissionNotAssignedException,
                                        PermissionNotFoundException,
                                        RoleNotFoundException)
from app.rbac.domain.interfaces import IPermissionRepository, IRoleRepository


class AssignPermissionToRoleUseCase:
    def __init__(
        self,
        role_repo: IRoleRepository,
        permission_repo: IPermissionRepository,
    ):
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    async def execute(self, role_id: int, permission_id: int) -> None:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFoundException(role_id)

        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundException(permission_id)

        # Logic to append to association table is pushed to the repository for DB efficiency
        await self.role_repo.add_permission(role_id, permission_id)


class RemovePermissionFromRoleUseCase:
    def __init__(
        self,
        role_repo: IRoleRepository,
        permission_repo: IPermissionRepository,
    ):
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    async def execute(self, role_id: int, permission_id: int) -> None:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFoundException(role_id)

        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundException(permission_id)

        # Let the repo handle removal. Optionally verify if it actually was removed.
        await self.role_repo.remove_permission(role_id, permission_id)
