"""
Account Repository — infrastructure layer.
"""

from typing import Optional, cast, Any

from app.auth.domain.entity import Account as AccountEntity
from app.auth.infrastructure.model import AccountModel
from app.user.infrastructure.model import UserModel
from app.shared.infrastructure.base_repository import BaseRepository
from sqlmodel import Session, select


class AccountRepository(BaseRepository[AccountModel, AccountEntity]):
    def __init__(self, session: Session):
        super().__init__(session, AccountModel)

    def get_by_email(self, email: str) -> Optional[AccountEntity]:
        stmt = (
            select(AccountModel)
            .join(UserModel, cast(Any, AccountModel.user_id == UserModel.id))
            .where(cast(Any, UserModel.email == email))
        )
        model = self.session.exec(stmt)
        res = model.first()
        return res.to_entity() if res else None
