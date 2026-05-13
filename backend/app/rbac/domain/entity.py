"""
RBAC (Role Based Access Control) Domain Entities.

Provides core business objects decoupled from database ORMs.
"""

from enum import Enum
from typing import List, Optional

from app.shared.domain.base_entity import BaseEntity


class RoleType(str, Enum):
    """Role type enum"""

    ADMIN = "admin"  # Chủ nhiệm
    LEADER = "leader"  # Trưởng nhóm
    TEAMMATE = "teammate"  # Thành viên


class Permission(BaseEntity):
    """Permission entity."""

    name: str  # e.g., "user:read", "user:write"
    description: Optional[str] = None
    resource: str  # e.g., "user", "role", "permission"
    action: str  # e.g., "create", "read", "update", "delete"


class RolePermission(BaseEntity):
    """Link between a Role and a Permission."""

    role_id: int
    permission_id: int
    permission: Optional[Permission] = None


class RoleApiKey(BaseEntity):
    """API Key attached to a specific Role."""

    name: str
    key_hash: str
    prefix: str
    is_active: bool = True
    role_id: int
    role: Optional["Role"] = None


class Role(BaseEntity):
    """Role entity."""

    name: str
    description: Optional[str] = None
    role_permissions: List[RolePermission] = []
    api_keys: List[RoleApiKey] = []

    @property
    def permissions(self) -> List[Permission]:
        """Flatten related permissions for ease of access, excluding deleted ones."""
        return [
            rp.permission
            for rp in self.role_permissions
            if rp.permission and not rp.is_deleted and not rp.permission.is_deleted
        ]
