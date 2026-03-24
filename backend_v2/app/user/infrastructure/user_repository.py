from typing import List, Optional

from app.rbac.infrastructure.models import RoleModel
from app.user.domain.repository import IUserRepository
from app.user.domain.user_entity import User, UserStatus
from app.user.infrastructure.user_model import UserModel
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col


class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(UserModel).where(
            col(UserModel.id) == user_id, col(UserModel.is_deleted).is_(False)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(UserModel).where(
            col(UserModel.email) == email, col(UserModel.is_deleted).is_(False)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by(
        self, user_id: int | None = None, email: str | None = None
    ) -> Optional[User]:
        stmt = select(UserModel).where(col(UserModel.is_deleted).is_(False))
        if email:
            stmt = stmt.where(col(UserModel.email) == email)
        if user_id:
            stmt = stmt.where(col(UserModel.id) == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def create(self, user: User) -> User:
        model = UserModel.from_entity(user)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()

    async def update(self, user: User) -> User:
        model = UserModel.from_entity(user)
        model = await self.session.merge(model)
        await self.session.commit()
        return model.to_entity()

    async def delete(self, user_id: int) -> None:
        stmt = (
            update(UserModel)
            .where(col(UserModel.id) == user_id)
            .values(is_deleted=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        role: str | None = None,
        status: UserStatus | None = None,
    ) -> List[User]:
        stmt = select(UserModel).where(col(UserModel.is_deleted).is_(False))

        if search:
            stmt = stmt.where(
                or_(
                    col(UserModel.name).ilike(f"%{search}%"),
                    col(UserModel.email).ilike(f"%{search}%"),
                    col(UserModel.phone_number).ilike(f"%{search}%"),
                )
            )

        if role:
            # Tham chiếu tới RoleModel thay vì UserRoleModel (lỗi cũ)
            stmt = stmt.join(
                RoleModel, col(UserModel.role_id) == col(RoleModel.id)
            ).where(col(RoleModel.name) == role)

        if status:
            stmt = stmt.where(col(UserModel.status) == status)

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [model.to_entity() for model in models]
