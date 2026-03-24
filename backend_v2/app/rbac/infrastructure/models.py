from typing import List, Optional

from app.rbac.domain.entities import Permission, Role, RoleApiKey
from app.shared.base_model import TimestampMixin
from sqlmodel import Field, Relationship, SQLModel


# Association table modeled in SQLModel
class RolePermissionTable(SQLModel, table=True):
    __tablename__ = "role_permissions"

    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)


class PermissionModel(TimestampMixin, table=True):
    __tablename__ = "permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=255)
    resource: str = Field(max_length=100, index=True)
    action: str = Field(max_length=50)

    # Use string forward reference for linking roles
    roles: List["RoleModel"] = Relationship(
        back_populates="permissions", link_model=RolePermissionTable
    )

    def to_entity(self) -> Permission:
        return Permission(
            id=self.id,  # type: ignore
            name=self.name,
            description=self.description,
            resource=self.resource,
            action=self.action,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: Permission) -> "PermissionModel":
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            resource=entity.resource,
            action=entity.action,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_deleted=entity.is_deleted,
        )


class RoleModel(TimestampMixin, table=True):
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=255)

    permissions: List["PermissionModel"] = Relationship(
        back_populates="roles", link_model=RolePermissionTable
    )
    api_keys: List["RoleApiKeyModel"] = Relationship(back_populates="role")

    def to_entity(self) -> Role:
        return Role(
            id=self.id,  # type: ignore
            name=self.name,
            description=self.description,
            permissions=(
                [p.to_entity() for p in self.permissions]
                if getattr(self, "permissions", None) is not None
                else []
            ),
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: Role) -> "RoleModel":
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_deleted=entity.is_deleted,
        )


class RoleApiKeyModel(TimestampMixin, table=True):
    __tablename__ = "role_api_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    key_hash: str = Field(index=True)
    prefix: str = Field(max_length=10)
    is_active: bool = Field(default=True)

    role_id: int = Field(foreign_key="roles.id", index=True)

    # Back reference to RoleModel
    role: "RoleModel" = Relationship(back_populates="api_keys")

    def to_entity(self) -> RoleApiKey:
        return RoleApiKey(
            id=self.id,  # type: ignore
            name=self.name,
            key_hash=self.key_hash,
            prefix=self.prefix,
            is_active=self.is_active,
            role_id=self.role_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: RoleApiKey) -> "RoleApiKeyModel":
        return cls(
            id=entity.id,
            name=entity.name,
            key_hash=entity.key_hash,
            prefix=entity.prefix,
            is_active=entity.is_active,
            role_id=entity.role_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_deleted=entity.is_deleted,
        )
