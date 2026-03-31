from typing import Optional

from app.auth.application.dtos import UserAuthContextDTO
from app.auth.domain.interfaces import IAuthQueryService
from app.auth.infrastructure.account_model import AccountModel
from app.rbac.infrastructure.models import RoleModel
from app.user.domain.user_entity import UserStatus
from app.user.infrastructure.user_model import UserModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class SQLAlchemyAuthQueryService(IAuthQueryService):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_auth_context_by_email(
        self, email: str
    ) -> Optional[UserAuthContextDTO]:
        stmt = (
            select(UserModel, AccountModel, RoleModel)
            .outerjoin(AccountModel, UserModel.account_id == AccountModel.id)  # type: ignore[arg-type]
            .outerjoin(RoleModel, UserModel.role_id == RoleModel.id)  # type: ignore[arg-type]
            .options(selectinload(RoleModel.permissions))  # type: ignore[arg-type]
            .where(UserModel.email == email)  # type: ignore[arg-type]
            .where(UserModel.is_deleted == False)  # type: ignore[arg-type]  # noqa: E712
        )
        result = await self.session.execute(stmt)
        row = result.first()

        if not row:
            return None

        user_model, account_model, role_model = row

        # If user has an account
        hashed_password = account_model.hash_password if account_model else ""
        is_active = user_model.status == UserStatus.ACTIVE

        role_name = None
        permissions = []
        if role_model:
            role_name = role_model.name
            permissions = [p.name for p in role_model.permissions]

        return UserAuthContextDTO(
            id=user_model.id,
            email=user_model.email,
            hashed_password=hashed_password,
            is_active=is_active,
            name=user_model.name,
            avatar_url=user_model.avatar_url or "",
            role_name=role_name,
            permissions=permissions,
        )
