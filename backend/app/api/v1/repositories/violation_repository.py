from datetime import datetime
from typing import List, Optional

from app.api.v1.repositories.base import BaseRepository
from app.models import Violation
from sqlalchemy import desc, extract
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select


class ViolationRepository(BaseRepository[Violation]):
    """Repository for Violation operations"""

    def __init__(self, session: Session):
        super().__init__(session, Violation)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Violation]:
        """Get all violations with user details"""

        statement = (
            select(Violation)
            .options(
                joinedload(Violation.user),
                joinedload(Violation.creator),
                joinedload(Violation.updater),
            )
            .order_by(desc(Violation.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_by_user_id(
        self, user_id: int, month: Optional[int] = None, year: Optional[int] = None
    ) -> List[Violation]:
        """Get all violations by a specific user, optionally filtered by month/year"""
        statement = select(Violation).where(Violation.user_id == user_id)

        if month is not None:
            statement = statement.where(extract("month", Violation.created_at) == month)
        if year is not None:
            statement = statement.where(extract("year", Violation.created_at) == year)

        return list(self.session.exec(statement).all())

    def get_by_user_and_date(self, user_id: int, target_date) -> List[Violation]:
        """Get violations for a user on a specific date"""

        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        statement = (
            select(Violation)
            .where(
                Violation.user_id == user_id,
                Violation.date >= start,
                Violation.date <= end,
            )
            .options(
                joinedload(Violation.user),
            )
        )
        return list(self.session.exec(statement).all())

    def get_by_date(self, target_date) -> List[Violation]:
        """Get all violations on a specific date"""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        statement = (
            select(Violation)
            .where(
                Violation.date >= start,
                Violation.date <= end,
            )
            .options(
                joinedload(Violation.user),
                joinedload(Violation.creator),
                joinedload(Violation.updater),
            )
        )
        return list(self.session.exec(statement).all())

    def get_by_month(
        self, month: int, year: int, user_id: Optional[int] = None
    ) -> List[Violation]:
        """Get all violations in a specific month"""
        statement = select(Violation)
        if user_id:
            statement = statement.where(Violation.user_id == user_id)
        if month:
            statement = statement.where(extract("month", Violation.date) == month)
        if year:
            statement = statement.where(extract("year", Violation.date) == year)

        statement = statement.options(
            joinedload(Violation.user),
            joinedload(Violation.creator),
            joinedload(Violation.updater),
        )
        return list(self.session.exec(statement).all())
