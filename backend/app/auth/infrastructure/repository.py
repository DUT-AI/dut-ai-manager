"""
Account Repository — infrastructure layer.
"""

from typing import Optional

from app.auth.domain.entity import Account as AccountEntity
from app.auth.infrastructure.model import AccountModel
from sqlmodel import Session, select


class AccountRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, account_id: int) -> Optional[AccountEntity]:
        model = self.session.get(AccountModel, account_id)
        return model.to_entity() if model else None

    def save(self, entity: AccountEntity) -> AccountEntity:
        model = AccountModel.from_entity(entity)
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return model.to_entity()

    def update(self, entity: AccountEntity) -> Optional[AccountEntity]:
        model = self.session.get(AccountModel, entity.id)
        if not model:
            return None

        update_data = entity.model_dump(
            exclude={"id", "created_at", "updated_at"}, exclude_unset=True
        )
        for key, value in update_data.items():
            if hasattr(model, key):
                setattr(model, key, value)

        self.session.add(model)
        self.session.flush()
        return model.to_entity()

    def delete_by_id(self, account_id: int) -> bool:
        model = self.session.get(AccountModel, account_id)
        if not model:
            return False
        self.session.delete(model)
        self.session.flush()
        return True
