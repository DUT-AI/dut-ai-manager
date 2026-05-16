"""
Account Repository — infrastructure layer.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.domain.entity import Account as AccountEntity
from app.auth.infrastructure.model import AccountModel
from app.shared.infrastructure.base_repository import BaseRepository
from app.user.infrastructure.model import UserModel


class AccountRepository(BaseRepository[AccountModel, AccountEntity]):
    def __init__(self, session: Session):
        super().__init__(session, AccountModel)

    def get_by_email(self, email: str) -> AccountEntity | None:
        stmt = (
            select(AccountModel)
            .join(UserModel, AccountModel.user_id == UserModel.id)
            .where(UserModel.email == email)
        )
        model = self.session.scalars(stmt)
        res = model.first()
        return res.to_entity() if res else None
