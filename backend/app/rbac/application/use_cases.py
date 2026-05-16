import secrets

from app.rbac.application.dtos import (
    PermissionCreate,
    PermissionUpdate,
    RoleApiKeyCreate,
    RoleApiKeySecret,
    RoleCreate,
    RoleUpdate,
)
from app.rbac.domain.entity import Permission, Role, RoleApiKey, RolePermission
from app.rbac.infrastructure.repository import (
    PermissionRepository,
    RoleApiKeyRepository,
    RolePermissionRepository,
    RoleRepository,
)
from app.utils.password import get_password_hash, verify_password


class RoleUseCases:
    """Use cases for Role, Permission, and their links."""

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
    def get_all_roles(self) -> list[Role]:
        return self.role_repo.get_all_roles()

    def get_role(self, role_id: int) -> Role | None:
        return self.role_repo.get_role_with_permissions(role_id)

    def create_role(self, role_data: RoleCreate) -> Role:
        role = Role(name=role_data.name, description=role_data.description)
        return self.role_repo.save(role)

    def update_role(self, role_id: int, role_data: RoleUpdate) -> Role | None:
        role = self.role_repo.get_by_id(role_id)
        if not role:
            return None
        if role_data.name is not None:
            role.name = role_data.name
        if role_data.description is not None:
            role.description = role_data.description
        return self.role_repo.save(role)

    def delete_role(self, role_id: int) -> bool:
        return self.role_repo.delete_by_id(role_id)

    # --- Permission Operations ---
    def get_all_permissions(self) -> list[Permission]:
        return self.permission_repo.get_all_permissions()

    def create_permission(self, perm_data: PermissionCreate) -> Permission:
        perm = Permission(
            name=perm_data.name,
            description=perm_data.description,
            resource=perm_data.resource,
            action=perm_data.action,
        )
        return self.permission_repo.save(perm)

    def update_permission(
        self, perm_id: int, perm_data: PermissionUpdate
    ) -> Permission | None:
        perm = self.permission_repo.get_by_id(perm_id)
        if not perm:
            return None
        if perm_data.name is not None:
            perm.name = perm_data.name
        if perm_data.description is not None:
            perm.description = perm_data.description
        if perm_data.resource is not None:
            perm.resource = perm_data.resource
        if perm_data.action is not None:
            perm.action = perm_data.action
        return self.permission_repo.save(perm)

    def delete_permission(self, perm_id: int) -> bool:
        return self.permission_repo.delete_by_id(perm_id)

    # --- Role-Permission Linking ---
    def add_permission_to_role(self, role_id: int, perm_id: int) -> tuple[bool, str]:
        role = self.role_repo.get_by_id(role_id)
        perm = self.permission_repo.get_by_id(perm_id)
        if not role or not perm:
            return False, "Role or Permission not found"

        existing = self.role_permission_repo.get_by_role_and_permission(
            role_id, perm_id
        )
        if existing:
            return False, "Permission already assigned to this role"

        link = RolePermission(role_id=role_id, permission_id=perm_id, permission=perm)
        self.role_permission_repo.save(link)
        return True, "Permission assigned successfully"

    def remove_permission_from_role(
        self, role_id: int, perm_id: int
    ) -> tuple[bool, str]:
        link = self.role_permission_repo.get_by_role_and_permission(role_id, perm_id)
        if not link:
            return False, "Permission not assigned to this role"

        self.role_permission_repo.hard_delete(link)
        return True, "Permission removed successfully"


class RoleApiKeyUseCases:
    """Use cases for API Keys."""

    def __init__(
        self,
        api_key_repo: RoleApiKeyRepository,
        role_repo: RoleRepository,
    ):
        self.api_key_repo = api_key_repo
        self.role_repo = role_repo

    def create_api_key(
        self, data: RoleApiKeyCreate
    ) -> tuple[RoleApiKeySecret | None, str]:
        """
        Create a new API key for a role.
        """
        role = self.role_repo.get_by_id(data.role_id)
        if not role:
            return None, "Role not found"

        raw_key = f"sk-{secrets.token_urlsafe(32)}"
        key_hash = get_password_hash(raw_key)
        prefix = raw_key[:6]

        api_key = RoleApiKey(
            name=data.name,
            key_hash=key_hash,
            prefix=prefix,
            role_id=data.role_id,
            role=role,
        )
        saved_key = self.api_key_repo.save(api_key)
        assert saved_key.id is not None
        response = RoleApiKeySecret(
            id=saved_key.id,
            name=saved_key.name,
            prefix=saved_key.prefix,
            is_active=saved_key.is_active,
            created_at=saved_key.created_at,
            role_id=saved_key.role_id,
            secret_key=raw_key,
        )

        return response, ""

    def get_by_role(self, role_id: int) -> list[RoleApiKey]:
        """Get all API keys for a role"""
        return self.api_key_repo.get_by_role_id(role_id)

    def revoke_api_key(self, key_id: int) -> tuple[bool, str]:
        """Revoke (delete) an API key"""
        key = self.api_key_repo.get_by_id(key_id)
        if not key:
            return False, "API Key not found"

        assert key.id is not None
        self.api_key_repo.delete_by_id(key.id)
        return True, "API Key revoked successfully"

    def verify_api_key(self, raw_key: str) -> tuple[Role | None, RoleApiKey | None]:
        """
        Verify an API key and return the associated Role and ApiKey object.
        """
        if not raw_key.startswith("sk-"):
            return None, None

        prefix = raw_key[:6]
        candidates = self.api_key_repo.get_candidates_by_prefix(prefix)

        for key in candidates:
            if verify_password(raw_key, key.key_hash):
                role = self.role_repo.get_role_with_permissions(key.role_id)
                return role, key

        return None, None
