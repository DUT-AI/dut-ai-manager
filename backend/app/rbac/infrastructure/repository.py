from sqlalchemy.orm import Session

from app.rbac.domain.entity import Permission, Role, RoleApiKey, RolePermission
from app.rbac.infrastructure.model import (
    PermissionModel,
    RoleApiKeyModel,
    RoleModel,
    RolePermissionModel,
)
from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.shared.infrastructure.base_repository import BaseRepository


class RoleRepository(BaseRepository[RoleModel, Role]):
    """Clean Architecture Repository for Role operations."""

    def __init__(self, session: Session):
        super().__init__(session, RoleModel)

    def get_all_roles(self, skip: int = 0, limit: int = 100) -> list[Role]:
        """Get all roles with permissions using QuerySupport."""
        qs = build_query_support(
            skip=skip,
            limit=limit,
            include=["role_permissions", "role_permissions.permission"],
        )
        return self.get_all(qs)

    def get_role_with_permissions(self, role_id: int) -> Role | None:
        """Get role with its permissions using get_one."""
        qs = build_query_support(
            filters=[
                FilterCriterion(field="id", operator=FilterOperator.EQ, value=role_id)
            ],
            include=["role_permissions", "role_permissions.permission"],
        )
        return self.get_one(qs)

    def get_by_name(self, name: str) -> Role | None:
        """Get role by name."""
        qs = build_query_support(
            filters=[
                FilterCriterion(field="name", operator=FilterOperator.EQ, value=name)
            ]
        )
        return self.get_one(qs)

    def save(self, entity: Role) -> Role:
        """Save role (add or update) using BaseRepository."""
        if entity.id:
            return self.update(entity)
        else:
            return self.add(entity)


class PermissionRepository(BaseRepository[PermissionModel, Permission]):
    """Clean Architecture Repository for Permission operations."""

    def __init__(self, session: Session):
        super().__init__(session, PermissionModel)

    def get_all_permissions(self, skip: int = 0, limit: int = 100) -> list[Permission]:
        """Get all permissions using QuerySupport."""
        qs = build_query_support(skip=skip, limit=limit)
        return self.get_all(qs)

    def save(self, entity: Permission) -> Permission:
        """Save permission (add or update) using BaseRepository."""
        if entity.id:
            return self.update(entity)
        else:
            return self.add(entity)


class RolePermissionRepository(BaseRepository[RolePermissionModel, RolePermission]):
    """Clean Architecture Repository for RolePermission link operations."""

    def __init__(self, session: Session):
        super().__init__(session, RolePermissionModel)

    def get_by_role_and_permission(
        self, role_id: int, permission_id: int
    ) -> RolePermission | None:
        """Get link by role and permission IDs."""
        qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="role_id", operator=FilterOperator.EQ, value=role_id
                ),
                FilterCriterion(
                    field="permission_id",
                    operator=FilterOperator.EQ,
                    value=permission_id,
                ),
            ]
        )
        return self.get_one(qs)

    def save(self, entity: RolePermission) -> RolePermission:
        """Save role-permission link using BaseRepository."""
        if entity.id:
            return self.update(entity)
        else:
            return self.add(entity)


class RoleApiKeyRepository(BaseRepository[RoleApiKeyModel, RoleApiKey]):
    """Clean Architecture Repository for RoleApiKey operations."""

    def __init__(self, session: Session):
        super().__init__(session, RoleApiKeyModel)

    def get_by_key_hash(self, key_hash: str) -> RoleApiKey | None:
        """Get API key by hash."""
        qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="key_hash", operator=FilterOperator.EQ, value=key_hash
                ),
                FilterCriterion(
                    field="is_active", operator=FilterOperator.EQ, value=True
                ),
            ]
        )
        return self.get_one(qs)

    def get_by_role_id(self, role_id: int) -> list[RoleApiKey]:
        """Get all API keys for a role."""
        qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="role_id", operator=FilterOperator.EQ, value=role_id
                )
            ]
        )
        return self.get_all(qs)

    def get_candidates_by_prefix(self, prefix: str) -> list[RoleApiKey]:
        """Get all active API keys with matching prefix."""
        qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="prefix", operator=FilterOperator.EQ, value=prefix
                ),
                FilterCriterion(
                    field="is_active", operator=FilterOperator.EQ, value=True
                ),
            ],
            include=["role"],
        )
        return self.get_all(qs)

    def save(self, entity: RoleApiKey) -> RoleApiKey:
        """Save API key using BaseRepository."""
        if entity.id:
            return self.update(entity)
        else:
            return self.add(entity)
