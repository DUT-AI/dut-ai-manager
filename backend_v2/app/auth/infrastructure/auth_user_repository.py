from typing import Optional

from app.auth.domain.auth_user_entity import AuthUser
from app.auth.domain.interfaces import IAuthUserRepository
from app.auth.infrastructure.account_model import AccountModel
from app.user.infrastructure.user_model import UserModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AuthUserRepository(IAuthUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[AuthUser]:
        stmt = (
            select(UserModel, AccountModel)
            .outerjoin(AccountModel, UserModel.account_id == AccountModel.id)  # type: ignore
            .where(UserModel.email == email)  # type: ignore
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            return None

        user_model, account_model = row
        return self._to_domain(user_model, account_model)

    async def get_by_id(self, user_id: int) -> Optional[AuthUser]:
        stmt = (
            select(UserModel, AccountModel)
            .outerjoin(AccountModel, UserModel.account_id == AccountModel.id)  # type: ignore
            .where(UserModel.id == user_id)  # type: ignore
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            return None

        user_model, account_model = row
        return self._to_domain(user_model, account_model)

    async def update_password(self, user_id: int, new_hashed_password: str) -> None:
        user_model = await self.session.get(UserModel, user_id)
        if user_model and user_model.account_id:
            account_model = await self.session.get(AccountModel, user_model.account_id)
            if account_model:
                account_model.hash_password = new_hashed_password
                await self.session.flush()

    def _to_domain(
        self, user_model: UserModel, account_model: Optional[AccountModel]
    ) -> AuthUser:
        return AuthUser(
            id=user_model.id,  # type: ignore
            email=user_model.email,
            status=user_model.status,
            hashed_password=account_model.hash_password if account_model else "",
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
            is_deleted=user_model.is_deleted,
        )
