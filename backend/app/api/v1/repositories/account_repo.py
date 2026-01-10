from app.api.v1.repositories.base import BaseRepository
from app.models import Account
from sqlmodel import Session


class AccountRepository(BaseRepository[Account]):
    """Repository for Account operations"""

    def __init__(self, session: Session):
        super().__init__(session, Account)
