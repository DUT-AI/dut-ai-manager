from typing import List, Optional, Tuple

from app.api.v1.repositories.role_permission_repository import (
    RoleRepository,
    PermissionRepository,
    RolePermissionRepository,
)
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.schemas.role_permission import (
    RoleCreate,
    RoleUpdate,
    PermissionCreate,
    PermissionUpdate,
)


class RolePermissionService:
    """Service for managing Roles and Permissions"""

    def __init__(
            self,
            role_repo: RoleRepository,
            permission_repo: PermissionRepository,
            role_permission_repo: RolePermissionRepository,
    ):
        self.role_repo = role_repo
        self.permission_repo = permission_repo
        self.role_permission_repo = role_permission_repo

    # --- Role Operations ---
    def get_all_roles(self) -> List[Role]:
        return self.role_repo.get_all()

    def get_role(self, role_id: int) -> Optional[Role]:
        return self.role_repo.get_by_id(role_id)

    def create_role(self, role_data: RoleCreate) -> Role:
        role = Role(**role_data.model_dump())
        return self.role_repo.create(role)

    def update_role(self, role_id: int, role_data: RoleUpdate) -> Optional[Role]:
        role = self.role_repo.get_by_id(role_id)
        if not role:
            return None

        update_dict = role_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(role, key, value)

        return self.role_repo.update(role)

    def delete_role(self, role_id: int) -> bool:
        return self.role_repo.delete_by_id(role_id)

    # --- Permission Operations ---
    def get_all_permissions(self) -> List[Permission]:
        return self.permission_repo.get_all()

    def create_permission(self, perm_data: PermissionCreate) -> Permission:
        perm = Permission(**perm_data.model_dump())
        return self.permission_repo.create(perm)

    def update_permission(
            self, perm_id: int, perm_data: PermissionUpdate
    ) -> Optional[Permission]:
        perm = self.permission_repo.get_by_id(perm_id)
        if not perm:
            return None

        update_dict = perm_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(perm, key, value)

        return self.permission_repo.update(perm)

    def delete_permission(self, perm_id: int) -> bool:
        return self.permission_repo.delete_by_id(perm_id)

    # --- Role-Permission Linking ---
    def add_permission_to_role(self, role_id: int, perm_id: int) -> Tuple[bool, str]:
        # Check if exists
        role = self.role_repo.get_by_id(role_id)
        perm = self.permission_repo.get_by_id(perm_id)
        if not role or not perm:
            return False, "Role or Permission not found"

        # Check if already linked
        existing = self.role_permission_repo.get_by_role_and_permission(
            role_id, perm_id
        )
        if existing:
            return False, "Permission already assigned to this role"

        link = RolePermission(role_id=role_id, permission_id=perm_id)
        self.role_permission_repo.create(link)
        return True, "Permission assigned successfully"

    def remove_permission_from_role(
            self, role_id: int, perm_id: int
    ) -> Tuple[bool, str]:
        link = self.role_permission_repo.get_by_role_and_permission(role_id, perm_id)
        if not link:
            return False, "Permission not assigned to this role"

        self.role_permission_repo.delete(link)
        return True, "Permission removed successfully"
