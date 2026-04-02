from typing import Any, TYPE_CHECKING, List, Optional
from app.rbac.domain.entity import Permission, Role, RoleApiKey, RolePermission
from app.shared.infrastructure.base_model import TimestampMixin
from app.utils.datetime import get_current_utc7_time
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from app.user.infrastructure.model import UserModel


class PermissionModel(TimestampMixin, table=True):
    """Database ORM mapping to 'permissions' table."""

    __tablename__ = "permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=255)
    resource: str = Field(max_length=100, index=True)
    action: str = Field(max_length=50)

    role_permissions: List["RolePermissionModel"] = Relationship(
        back_populates="permission"
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
    def from_entity(cls, entity: Any) -> "PermissionModel":
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            resource=entity.resource,
            action=entity.action,
            created_at=entity.created_at or get_current_utc7_time(),
            updated_at=entity.updated_at or get_current_utc7_time(),
            is_deleted=entity.is_deleted or False,
        )


class RoleApiKeyModel(TimestampMixin, table=True):
    """Database ORM mapping to 'role_api_keys' table."""

    __tablename__ = "role_api_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    key_hash: str = Field(index=True)
    prefix: str = Field(max_length=10)
    is_active: bool = Field(default=True)
    role_id: int = Field(foreign_key="roles.id", index=True)

    role: "RoleModel" = Relationship(back_populates="api_keys")

    def to_entity(self) -> RoleApiKey:
        # Only include role if it's already loaded to avoid N+1
        role_entity = None
        if "role" in self.__dict__:
             if self.role:
                 role_entity = self.role.to_entity()

        return RoleApiKey(
            id=self.id,  # type: ignore
            name=self.name,
            key_hash=self.key_hash,
            prefix=self.prefix,
            is_active=self.is_active,
            role_id=self.role_id,
            role=role_entity,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: Any) -> "RoleApiKeyModel":
        return cls(
            id=entity.id,
            name=entity.name,
            key_hash=entity.key_hash,
            prefix=entity.prefix,
            is_active=entity.is_active,
            role_id=entity.role_id,
            created_at=entity.created_at or get_current_utc7_time(),
            updated_at=entity.updated_at or get_current_utc7_time(),
            is_deleted=entity.is_deleted or False,
        )


class RolePermissionModel(TimestampMixin, table=True):
    """Database ORM for the many-to-many relationship."""

    __tablename__ = "role_permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key="roles.id", index=True)
    permission_id: int = Field(foreign_key="permissions.id", index=True)

    role: Optional["RoleModel"] = Relationship(back_populates="role_permissions")
    permission: Optional["PermissionModel"] = Relationship(
        back_populates="role_permissions"
    )

    def to_entity(self) -> RolePermission:
        # Only include permission if it's already loaded to avoid N+1
        perm_entity = None
        if "permission" in self.__dict__:
             if self.permission:
                 perm_entity = self.permission.to_entity()

        return RolePermission(
            id=self.id,  # type: ignore
            role_id=self.role_id,
            permission_id=self.permission_id,
            permission=perm_entity,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: Any) -> "RolePermissionModel":
        return cls(
            id=entity.id,
            role_id=entity.role_id,
            permission_id=entity.permission_id,
            created_at=entity.created_at or get_current_utc7_time(),
            updated_at=entity.updated_at or get_current_utc7_time(),
            is_deleted=entity.is_deleted or False,
        )


class RoleModel(TimestampMixin, table=True):
    """Database ORM mapping to 'roles' table."""

    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=255)

    users: List["UserModel"] = Relationship(
        back_populates="role",
        sa_relationship_kwargs={"foreign_keys": "[UserModel.role_id]"},
    )
    role_permissions: List["RolePermissionModel"] = Relationship(back_populates="role")
    api_keys: List["RoleApiKeyModel"] = Relationship(back_populates="role")

    def to_entity(self) -> Role:
        role_permissions = []
        if "role_permissions" in self.__dict__:
            role_permissions = [rp.to_entity() for rp in self.role_permissions]

        api_keys = []
        if "api_keys" in self.__dict__:
            api_keys = [k.to_entity() for k in self.api_keys]

        return Role(
            id=self.id,
            name=self.name,
            description=self.description,
            role_permissions=role_permissions,
            api_keys=api_keys,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted,
        )

    @classmethod
    def from_entity(cls, entity: Any) -> "RoleModel":
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at or get_current_utc7_time(),
            updated_at=entity.updated_at or get_current_utc7_time(),
            is_deleted=entity.is_deleted or False,
        )
