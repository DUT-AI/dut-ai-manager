from typing import List, Optional

from app.api.v1.repositories.base import BaseRepository
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select


class RoleRepository(BaseRepository[Role]):
    """Repository for Role operations"""

    def __init__(self, session: Session):
        super().__init__(session, Role)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """Get all roles with permissions"""
        from sqlalchemy.orm import selectinload

        statement = (
            select(Role)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Role.role_permissions).selectinload(
                    RolePermission.permission
                )
            )
        )
        return list(self.session.exec(statement).all())

    def get_role_with_permissions(self, role_id: int) -> Optional[Role]:
        """Get role with its permissions"""
        statement = (
            select(Role)
            .where(Role.id == role_id)
            .options(
                selectinload(Role.role_permissions).selectinload(
                    RolePermission.permission
                )
            )
        )
        return self.session.exec(statement).first()


class PermissionRepository(BaseRepository[Permission]):
    """Repository for Permission operations"""

    def __init__(self, session: Session):
        super().__init__(session, Permission)


class RolePermissionRepository(BaseRepository[RolePermission]):
    """Repository for RolePermission link operations"""

    def __init__(self, session: Session):
        super().__init__(session, RolePermission)

    def get_by_role_and_permission(
            self, role_id: int, permission_id: int
    ) -> Optional[RolePermission]:
        """Get link by role and permission IDs"""
        statement = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
        return self.session.exec(statement).first()
