from typing import Optional

from app.rbac.domain.entities import Permission, Role, RoleApiKey
from app.rbac.domain.interfaces import (IPermissionRepository,
                                        IRoleApiKeyRepository, IRoleRepository)
from app.rbac.infrastructure.models import (PermissionModel, RoleApiKeyModel,
                                            RoleModel)
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col


class SQLAlchemyRoleRepository(IRoleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Role]:
        stmt = (
            select(RoleModel)
            .where(col(RoleModel.is_deleted).is_(False))
            .options(selectinload(RoleModel.permissions))  # type: ignore
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_id(self, role_id: int) -> Optional[Role]:
        stmt = (
            select(RoleModel)
            .where(RoleModel.id == role_id)  # type: ignore
            .where(col(RoleModel.is_deleted).is_(False))
            .options(selectinload(RoleModel.permissions))  # type: ignore
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_name(self, name: str) -> Optional[Role]:
        stmt = (
            select(RoleModel)
            .where(RoleModel.name == name)  # type: ignore
            .where(col(RoleModel.is_deleted).is_(False))
            .options(selectinload(RoleModel.permissions))  # type: ignore
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def create(self, role: Role) -> Role:
        model = RoleModel(name=role.name, description=role.description)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, role: Role) -> Role:
        stmt = select(RoleModel).where(RoleModel.id == role.id)  # type: ignore
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        model.name = role.name
        model.description = role.description
        await self.session.flush()

        await self.session.refresh(model, ["permissions"])
        return model.to_entity()

    async def delete(self, role_id: int) -> bool:
        stmt = select(RoleModel).where(RoleModel.id == role_id)  # type: ignore
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.is_deleted = True
            await self.session.flush()
            return True
        return False

    async def add_permission(self, role_id: int, permission_id: int) -> bool:
        stmt = (
            select(RoleModel)
            .where(RoleModel.id == role_id)  # type: ignore
            .options(selectinload(RoleModel.permissions))  # type: ignore
        )
        result = await self.session.execute(stmt)
        role_model = result.scalar_one_or_none()
        if not role_model:
            return False

        perm_stmt = select(PermissionModel).where(PermissionModel.id == permission_id)  # type: ignore
        perm_result = await self.session.execute(perm_stmt)
        perm_model = perm_result.scalar_one_or_none()
        if not perm_model:
            return False

        if perm_model not in role_model.permissions:
            role_model.permissions.append(perm_model)
            await self.session.flush()
        return True

    async def remove_permission(self, role_id: int, permission_id: int) -> bool:
        stmt = (
            select(RoleModel)
            .where(RoleModel.id == role_id)  # type: ignore
            .options(selectinload(RoleModel.permissions))  # type: ignore
        )
        result = await self.session.execute(stmt)
        role_model = result.scalar_one_or_none()
        if not role_model:
            return False

        role_model.permissions = [
            p for p in role_model.permissions if p.id != permission_id  # type: ignore
        ]
        await self.session.flush()
        return True


class SQLAlchemyPermissionRepository(IPermissionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Permission]:
        stmt = select(PermissionModel).where(col(PermissionModel.is_deleted).is_(False))
        result = await self.session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def get_by_id(self, permission_id: int) -> Optional[Permission]:
        stmt = (
            select(PermissionModel)
            .where(PermissionModel.id == permission_id)  # type: ignore
            .where(col(PermissionModel.is_deleted).is_(False))
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_name(self, name: str) -> Optional[Permission]:
        stmt = (
            select(PermissionModel)
            .where(PermissionModel.name == name)  # type: ignore
            .where(col(PermissionModel.is_deleted).is_(False))
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def create(self, permission: Permission) -> Permission:
        model = PermissionModel(
            name=permission.name,
            description=permission.description,
            resource=permission.resource,
            action=permission.action,
        )
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, permission: Permission) -> Permission:
        stmt = select(PermissionModel).where(PermissionModel.id == permission.id)  # type: ignore
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        model.name = permission.name
        model.description = permission.description
        await self.session.flush()
        return model.to_entity()

    async def delete(self, permission_id: int) -> bool:
        stmt = select(PermissionModel).where(PermissionModel.id == permission_id)  # type: ignore
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.is_deleted = True
            await self.session.flush()
            return True
        return False


class SQLAlchemyRoleApiKeyRepository(IRoleApiKeyRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_role_id(self, role_id: int) -> list[RoleApiKey]:
        stmt = (
            select(RoleApiKeyModel)
            .where(RoleApiKeyModel.role_id == role_id)  # type: ignore
            .where(col(RoleApiKeyModel.is_deleted).is_(False))
        )
        result = await self.session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def get_by_id(self, key_id: int) -> Optional[RoleApiKey]:
        stmt = (
            select(RoleApiKeyModel)
            .where(RoleApiKeyModel.id == key_id)  # type: ignore
            .where(col(RoleApiKeyModel.is_deleted).is_(False))
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def create(self, api_key: RoleApiKey) -> RoleApiKey:
        model = RoleApiKeyModel(
            name=api_key.name,
            key_hash=api_key.key_hash,
            prefix=api_key.prefix,
            is_active=api_key.is_active,
            role_id=api_key.role_id,
        )
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def delete(self, key_id: int) -> bool:
        stmt = select(RoleApiKeyModel).where(RoleApiKeyModel.id == key_id)  # type: ignore
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False
