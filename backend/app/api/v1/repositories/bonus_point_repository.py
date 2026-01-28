from datetime import datetime
from typing import List, Optional

from app.api.v1.repositories.base import BaseRepository
from app.models.bonus_points import BonusPoint
from sqlalchemy import extract
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select


class BonusPointRepository(BaseRepository[BonusPoint]):
    """Repository for BonusPoint operations"""

    def __init__(self, session: Session):
        super().__init__(session, BonusPoint)

    def get_by_user_id(
        self, user_id: int, month: Optional[int] = None, year: Optional[int] = None
    ) -> List[BonusPoint]:
        """Get all bonus points by a specific user, optionally filtered by month/year"""
        statement = select(BonusPoint).where(
            BonusPoint.is_deleted == False, BonusPoint.user_id == user_id
        )

        if month is not None:
            statement = statement.where(
                extract("month", BonusPoint.created_at) == month
            )
        if year is not None:
            statement = statement.where(extract("year", BonusPoint.created_at) == year)

        statement.sort_by(BonusPoint.created_at)

        return list(self.session.exec(statement).all())

    def get_by_user_and_date(self, user_id: int, target_date) -> List[BonusPoint]:
        """Get bonus points for a user on a specific date"""

        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        statement = (
            select(BonusPoint)
            .where(
                BonusPoint.is_deleted == False,
                BonusPoint.user_id == user_id,
                BonusPoint.date >= start,
                BonusPoint.date <= end,
            )
            .options(
                joinedload(BonusPoint.user),
            )
            .sort_by(BonusPoint.created_at)
        )
        return list(self.session.exec(statement).all())

    def get_by_date(self, target_date) -> List[BonusPoint]:
        """Get all bonus points on a specific date"""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        statement = (
            select(BonusPoint)
            .where(
                BonusPoint.is_deleted == False,
                BonusPoint.date >= start,
                BonusPoint.date <= end,
            )
            .options(
                joinedload(BonusPoint.user),
                joinedload(BonusPoint.creator),
                joinedload(BonusPoint.updater),
            )
        )
        return list(self.session.exec(statement).all())

    def get_by_month(
        self, month: int, year: int, user_id: Optional[int] = None
    ) -> List[BonusPoint]:
        """Get all bonus points in a specific month"""
        statement = select(BonusPoint).where(BonusPoint.is_deleted == False)
        if user_id:
            statement = statement.where(BonusPoint.user_id == user_id)
        if month:
            statement = statement.where(extract("month", BonusPoint.date) == month)
        if year:
            statement = statement.where(extract("year", BonusPoint.date) == year)

        statement = statement.options(
            joinedload(BonusPoint.user),
            joinedload(BonusPoint.creator),
            joinedload(BonusPoint.updater),
        )
        return list(self.session.exec(statement).all())
