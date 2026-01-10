from typing import Optional

from app.api.v1.repositories import BaseRepository
from app.models import User
from sqlmodel import Session, select


class UserRepository(BaseRepository[User]):
    """Repository for User operations"""

    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def get_by_account_id(self, account_id: int) -> Optional[User]:
        """Get user by account ID"""
        statement = select(User).where(User.account_id == account_id)
        return self.session.exec(statement).first()
