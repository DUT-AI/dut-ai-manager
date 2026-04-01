from typing import List, Optional

from app.rbac.domain.entity import Permission, Role, RoleApiKey, RolePermission
from app.rbac.infrastructure.model import (PermissionModel, RoleApiKeyModel,
                                           RoleModel, RolePermissionModel)
from app.shared.infrastructure.base_repository import BaseRepository
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select


class RoleRepository(BaseRepository[RoleModel]):
    """Clean Architecture Repository for Role operations."""

    def __init__(self, session: Session):
        super().__init__(session, RoleModel)

    def to_entity(self, model: Optional[RoleModel]) -> Optional[Role]:
        if model is None:
            return None
        return model.to_entity()

    def from_entity(self, entity: Role) -> RoleModel:
        return RoleModel.from_entity(entity)

    def get_all_roles(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """Get all roles with permissions."""
        statement = (
            select(RoleModel)
            .where(RoleModel.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(RoleModel.role_permissions).selectinload(
                    RolePermissionModel.permission
                )
            )
        )
        models = list(self.session.exec(statement).all())
        return [self.to_entity(m) for m in models]  # type: ignore

    def get_role_with_permissions(self, role_id: int) -> Optional[Role]:
        """Get role with its permissions."""
        statement = (
            select(RoleModel)
            .where(
                RoleModel.is_deleted == False,
                RoleModel.id == role_id,
            )
            .options(
                selectinload(RoleModel.role_permissions).selectinload(
                    RolePermissionModel.permission
                )
            )
        )
        model = self.session.exec(statement).first()
        return self.to_entity(model)

    def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        statement = select(RoleModel).where(
            RoleModel.is_deleted == False, RoleModel.name == name
        )
        model = self.session.exec(statement).first()
        return self.to_entity(model)

    def save(self, entity: Role) -> Role:
        model = self.from_entity(entity)
        if model.id:
            updated_model = self.update(model)
            return self.to_entity(updated_model)  # type: ignore
        else:
            created_model = self.add(model)
            self.session.flush()
            return self.to_entity(created_model)  # type: ignore


class PermissionRepository(BaseRepository[PermissionModel]):
    """Clean Architecture Repository for Permission operations."""

    def __init__(self, session: Session):
        super().__init__(session, PermissionModel)

    def to_entity(self, model: Optional[PermissionModel]) -> Optional[Permission]:
        if model is None:
            return None
        return model.to_entity()

    def from_entity(self, entity: Permission) -> PermissionModel:
        return PermissionModel.from_entity(entity)

    def get_all_permissions(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        models = self.get_all(skip=skip, limit=limit)
        return [self.to_entity(m) for m in models]  # type: ignore

    def save(self, entity: Permission) -> Permission:
        model = self.from_entity(entity)
        if model.id:
            updated_model = self.update(model)
            return self.to_entity(updated_model)  # type: ignore
        else:
            created_model = self.add(model)
            self.session.flush()
            return self.to_entity(created_model)  # type: ignore

    def get_by_id_entity(self, id: int) -> Optional[Permission]:
        model = self.get_by_id(id)
        return self.to_entity(model)


class RolePermissionRepository(BaseRepository[RolePermissionModel]):
    """Clean Architecture Repository for RolePermission link operations."""

    def __init__(self, session: Session):
        super().__init__(session, RolePermissionModel)

    def to_entity(
        self, model: Optional[RolePermissionModel]
    ) -> Optional[RolePermission]:
        if model is None:
            return None
        return model.to_entity()

    def from_entity(self, entity: RolePermission) -> RolePermissionModel:
        return RolePermissionModel.from_entity(entity)

    def get_by_role_and_permission(
        self, role_id: int, permission_id: int
    ) -> Optional[RolePermission]:
        """Get link by role and permission IDs."""
        statement = select(RolePermissionModel).where(
            RolePermissionModel.is_deleted == False,
            RolePermissionModel.role_id == role_id,
            RolePermissionModel.permission_id == permission_id,
        )
        model = self.session.exec(statement).first()
        return self.to_entity(model)

    def save(self, entity: RolePermission) -> RolePermission:
        model = self.from_entity(entity)
        if model.id:
            updated_model = self.update(model)
            return self.to_entity(updated_model)  # type: ignore
        else:
            created_model = self.add(model)
            self.session.flush()
            return self.to_entity(created_model)  # type: ignore

    def get_by_id_entity(self, id: int) -> Optional[RolePermission]:
        model = self.get_by_id(id)
        return self.to_entity(model)


class RoleApiKeyRepository(BaseRepository[RoleApiKeyModel]):
    """Clean Architecture Repository for RoleApiKey operations."""

    def __init__(self, session: Session):
        super().__init__(session, RoleApiKeyModel)

    def to_entity(self, model: Optional[RoleApiKeyModel]) -> Optional[RoleApiKey]:
        if model is None:
            return None
        return model.to_entity()

    def from_entity(self, entity: RoleApiKey) -> RoleApiKeyModel:
        return RoleApiKeyModel.from_entity(entity)

    def get_by_key_hash(self, key_hash: str) -> Optional[RoleApiKey]:
        """Get API key by hash."""
        statement = select(RoleApiKeyModel).where(
            RoleApiKeyModel.is_deleted == False,
            RoleApiKeyModel.key_hash == key_hash,
            RoleApiKeyModel.is_active == True,
        )
        model = self.session.exec(statement).first()
        return self.to_entity(model)

    def get_by_role_id(self, role_id: int) -> list[RoleApiKey]:
        """Get all API keys for a role."""
        statement = select(RoleApiKeyModel).where(
            RoleApiKeyModel.is_deleted == False,
            RoleApiKeyModel.role_id == role_id,
        )
        models = list(self.session.exec(statement).all())
        return [self.to_entity(m) for m in models]  # type: ignore

    def get_candidates_by_prefix(self, prefix: str) -> list[RoleApiKey]:
        """Get all active API keys with matching prefix."""
        statement = (
            select(RoleApiKeyModel)
            .where(
                RoleApiKeyModel.is_deleted == False,
                RoleApiKeyModel.prefix == prefix,
                RoleApiKeyModel.is_active == True,
            )
            .options(selectinload(RoleApiKeyModel.role))
        )
        models = list(self.session.exec(statement).all())
        return [self.to_entity(m) for m in models]  # type: ignore

    def save(self, entity: RoleApiKey) -> RoleApiKey:
        model = self.from_entity(entity)
        if model.id:
            updated_model = self.update(model)
            return self.to_entity(updated_model)  # type: ignore
        else:
            created_model = self.add(model)
            self.session.flush()
            return self.to_entity(created_model)  # type: ignore

    def get_by_id_entity(self, id: int) -> Optional[RoleApiKey]:
        model = self.get_by_id(id)
        return self.to_entity(model)
