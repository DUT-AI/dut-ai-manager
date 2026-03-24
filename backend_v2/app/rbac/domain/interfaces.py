from typing import Optional, Protocol

from app.rbac.domain.entities import Permission, Role, RoleApiKey


class IRoleRepository(Protocol):
    async def get_all(self) -> list[Role]:
        """Get all roles."""
        ...

    async def get_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        ...

    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        ...

    async def create(self, role: Role) -> Role:
        """Create a new role."""
        ...

    async def update(self, role: Role) -> Role:
        """Update an existing role."""
        ...

    async def delete(self, role_id: int) -> bool:
        """Delete a role by ID."""
        ...

    async def add_permission(self, role_id: int, permission_id: int) -> bool:
        """Add a permission to a role."""
        ...

    async def remove_permission(self, role_id: int, permission_id: int) -> bool:
        """Remove a permission from a role."""
        ...


class IPermissionRepository(Protocol):
    async def get_all(self) -> list[Permission]:
        """Get all permissions."""
        ...

    async def get_by_id(self, permission_id: int) -> Optional[Permission]:
        """Get permission by ID."""
        ...

    async def get_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name."""
        ...

    async def create(self, permission: Permission) -> Permission:
        """Create a new permission."""
        ...

    async def update(self, permission: Permission) -> Permission:
        """Update an existing permission."""
        ...

    async def delete(self, permission_id: int) -> bool:
        """Delete a permission by ID."""
        ...


class IRoleApiKeyRepository(Protocol):
    async def get_by_role_id(self, role_id: int) -> list[RoleApiKey]:
        """Get all API keys for a specific role."""
        ...

    async def get_by_id(self, key_id: int) -> Optional[RoleApiKey]:
        """Get an API key by its ID."""
        ...

    async def create(self, api_key: RoleApiKey) -> RoleApiKey:
        """Create a new API key."""
        ...

    async def delete(self, key_id: int) -> bool:
        """Revoke/Delete an API key."""
        ...
