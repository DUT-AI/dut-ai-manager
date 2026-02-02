from sqlalchemy import func
from typing import List, Optional

from app.api.v1.repositories.base import BaseRepository
from app.models import RequestCategory
from app.models.permission_request import PermissionRequest
from sqlalchemy import desc, extract
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select


class PermissionRequestRepository(BaseRepository[PermissionRequest]):
    """Repository for PermissionRequest operations"""

    def __init__(self, session: Session):
        super().__init__(session, PermissionRequest)

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> List[PermissionRequest]:
        """Get all permission requests"""

        statement = (
            select(PermissionRequest)
            .where(PermissionRequest.is_deleted == deleted)
            .options(
                joinedload(PermissionRequest.creator),
                joinedload(PermissionRequest.updater),
            )
            .order_by(desc(PermissionRequest.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_by_created_by(
        self,
        user_id: int,
        month: Optional[int] = None,
        year: Optional[int] = None,
        deleted: bool = False,
    ) -> List[PermissionRequest]:
        """Get all requests created by a specific user, optionally filtered by month/year"""
        statement = select(PermissionRequest).where(
            PermissionRequest.is_deleted == deleted,
            PermissionRequest.created_by == user_id,
        )

        if month is not None:
            statement = statement.where(
                extract("month", PermissionRequest.created_at) == month
            )
        if year is not None:
            statement = statement.where(
                extract("year", PermissionRequest.created_at) == year
            )

        return list(self.session.exec(statement).all())

    def get_by_user_and_date(
        self, user_id: int, target_date
    ) -> List[PermissionRequest]:
        """Get permission requests for a user on a specific date"""
        statement = select(PermissionRequest).where(
            PermissionRequest.is_deleted == False,
            PermissionRequest.created_by == user_id,
            PermissionRequest.date == target_date,
        )
        return list(self.session.exec(statement).all())

    def get_by_date(self, target_date) -> List[PermissionRequest]:
        """Get all permission requests on a specific date"""
        statement = (
            select(PermissionRequest)
            .where(PermissionRequest.is_deleted == False)
            .where(PermissionRequest.date == target_date)
            .options(
                joinedload(PermissionRequest.creator),
                joinedload(PermissionRequest.updater),
            )
        )
        return list(self.session.exec(statement).all())

    def get_by_month(self, month: int, year: int) -> List[PermissionRequest]:
        """Get all permission requests in a specific month"""
        statement = select(PermissionRequest).where(
            PermissionRequest.is_deleted == False
        )
        if month:
            statement = statement.where(
                extract("month", PermissionRequest.date) == month
            )
        if year:
            statement = statement.where(extract("year", PermissionRequest.date) == year)

        statement = statement.options(
            joinedload(PermissionRequest.creator),
            joinedload(PermissionRequest.updater),
        )
        return list(self.session.exec(statement).all())

    def count_by_user_category_month(
        self, user_id: int, category: RequestCategory, month: int, year: int
    ) -> int:
        """Count permission requests by user, category, and month"""
        statement = (
            select(func.count())
            .select_from(PermissionRequest)
            .where(
                PermissionRequest.is_deleted == False,
                PermissionRequest.created_by == user_id,
                PermissionRequest.category == category,
                extract("month", PermissionRequest.date) == month,
                extract("year", PermissionRequest.date) == year,
            )
        )
        return self.session.exec(statement).one()

    def has_postpone_request_for_date(self, user_id: int, target_date) -> bool:
        """
        Check if user has a POSTPONE permission request for specific date.
        Used by the scheduled homework checker job.
        """
        statement = (
            select(func.count())
            .select_from(PermissionRequest)
            .where(
                PermissionRequest.is_deleted == False,
                PermissionRequest.created_by == user_id,
                PermissionRequest.category == RequestCategory.POSTPONE,
                PermissionRequest.date == target_date,
            )
        )
        count = self.session.exec(statement).one()
        return count > 0
