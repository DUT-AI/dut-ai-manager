"""
Violation Repository — data access layer.

Uses flush() instead of commit(). Session commits at middleware level.
Mapping delegated to ViolationModel.to_entity() / .from_entity().
"""

from datetime import date, datetime, time
from typing import Any

from sqlalchemy import desc, extract, select, update
from sqlalchemy.orm import Session, joinedload

from app.shared.infrastructure.base_repository import BaseRepository
from app.utils.datetime import get_current_utc7_time
from app.violation.domain.entity import Violation
from app.violation.infrastructure.model import ViolationModel


class ViolationRepository(BaseRepository[ViolationModel, Violation]):
    """Concrete repository using BaseRepository logic."""

    def __init__(self, session: Session):
        super().__init__(session, ViolationModel)

    def get_all(
        self,
        query_support: Any | None = None,
        deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Violation]:
        """Override get_all to include default relations and support skip/limit if no query_support."""
        statement = select(ViolationModel).where(ViolationModel.is_deleted == deleted)

        # Default includes
        statement = statement.options(
            joinedload(ViolationModel.user),
            joinedload(ViolationModel.creator_rel),
            joinedload(ViolationModel.updater_rel),
        )

        if query_support:
            from app.shared.domain.query_support import apply_query_support

            statement = apply_query_support(statement, ViolationModel, query_support)
        else:
            # Default sorting for Trash
            sort_field = (
                ViolationModel.updated_at if deleted else ViolationModel.created_at
            )
            statement = statement.order_by(desc(sort_field))
            statement = statement.offset(skip).limit(limit)

        results = self.session.scalars(statement).unique().all()
        return [m.to_entity() for m in results]

    def get_by_month(
        self,
        month: int | None = None,
        year: int | None = None,
        user_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Violation]:
        """Get violations filtered by month/year/user/date range."""
        statement = select(ViolationModel).where(ViolationModel.is_deleted == False)  # noqa: E712

        if user_id:
            statement = statement.where(ViolationModel.user_id == user_id)
        if start_date is not None:
            statement = statement.where(ViolationModel.date >= start_date)
        if end_date is not None:
            statement = statement.where(ViolationModel.date <= end_date)
        if month is not None:
            statement = statement.where(extract("month", ViolationModel.date) == month)
        if year is not None:
            statement = statement.where(extract("year", ViolationModel.date) == year)

        statement = statement.options(
            joinedload(ViolationModel.user),
            joinedload(ViolationModel.creator_rel),
            joinedload(ViolationModel.updater_rel),
        ).order_by(desc(ViolationModel.date))

        return [m.to_entity() for m in self.session.scalars(statement).unique().all()]

    def get_by_date(self, target_date: date) -> list[Violation]:
        """Get all violations on a specific date (accepts date or datetime)."""
        # Tránh lỗi type hint nếu target_date là datetime
        d = target_date.date() if isinstance(target_date, datetime) else target_date
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)

        statement = (
            select(ViolationModel)
            .where(
                ViolationModel.is_deleted == False,  # noqa: E712
                ViolationModel.date >= start,
                ViolationModel.date <= end,
            )
            .options(
                joinedload(ViolationModel.user),
                joinedload(ViolationModel.creator_rel),
                joinedload(ViolationModel.updater_rel),
            )
        )
        return [m.to_entity() for m in self.session.scalars(statement).unique().all()]

    def get_by_user_and_date(self, user_id: int, target_date: date) -> list[Violation]:
        """Get violations for a specific user on a specific date."""
        d = target_date.date() if isinstance(target_date, datetime) else target_date
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)

        statement = (
            select(ViolationModel)
            .where(
                ViolationModel.is_deleted == False,  # noqa: E712
                ViolationModel.user_id == user_id,
                ViolationModel.date >= start,
                ViolationModel.date <= end,
            )
            .options(
                joinedload(ViolationModel.user),
            )
        )
        return [m.to_entity() for m in self.session.scalars(statement).unique().all()]

    def save(self, entity: Violation) -> Violation:
        """Compatibility save method."""
        if entity.id:
            return self.update(entity)
        return self.add(entity)

    def save_all(self, entities: list[Violation]) -> list[Violation]:
        """Save multiple violations in batch with eager loading to avoid N+1."""
        if not entities:
            return []

        models = [ViolationModel.from_entity(e) for e in entities]
        for m in models:
            self.session.add(m)
        self.session.flush()

        # Reload with relationships in one batch query
        ids = [m.id for m in models]
        statement = (
            select(ViolationModel)
            .where(ViolationModel.id.in_(ids))
            .options(
                joinedload(ViolationModel.user),
                joinedload(ViolationModel.creator_rel),
                joinedload(ViolationModel.updater_rel),
            )
        )

        reloaded = self.session.scalars(statement).unique().all()
        # Sort back to match original order if needed, but usually not critical for violations
        return [m.to_entity() for m in reloaded]

    def get_aggregated_report(
        self,
        month: int | None = None,
        year: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        keyword: str | None = None,
    ) -> list[dict]:
        """Tổng hợp vi phạm theo user (chỉ tính count)."""

        from sqlalchemy import extract, func, or_

        from app.user.infrastructure.model import UserModel

        stmt = (
            select(
                UserModel.id.label("user_id"),
                UserModel.name.label("name"),
                UserModel.email.label("email"),
                UserModel.avatar_url.label("avatar_url"),
                UserModel.status.label("status"),
                UserModel.phone_number.label("phone_number"),
                func.count(ViolationModel.id).label("total_violations"),
                func.count(ViolationModel.id).label("details_count"),
            )
            .join(ViolationModel, ViolationModel.user_id == UserModel.id)
            .where(
                ViolationModel.is_deleted.is_(False),
                UserModel.is_deleted.is_(False),
            )
            .group_by(
                UserModel.id,
                UserModel.name,
                UserModel.email,
                UserModel.avatar_url,
                UserModel.status,
                UserModel.phone_number,
            )
            .order_by(func.count(ViolationModel.id).desc())
        )

        if start_date:
            stmt = stmt.where(ViolationModel.date >= start_date)
        if end_date:
            stmt = stmt.where(ViolationModel.date <= end_date)
        if month:
            stmt = stmt.where(extract("month", ViolationModel.date) == month)
        if year:
            stmt = stmt.where(extract("year", ViolationModel.date) == year)
        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            stmt = stmt.where(
                or_(
                    UserModel.name.ilike(kw),
                    UserModel.email.ilike(kw),
                )
            )

        rows = self.session.execute(stmt).all()
        return [
            {
                "user_id": r.user_id,
                "name": r.name,
                "email": r.email,
                "avatar_url": r.avatar_url,
                "status": r.status,
                "phone_number": r.phone_number,
                "total_violations": int(r.total_violations or 0),
                "details_count": int(r.details_count or 0),
            }
            for r in rows
        ]

    def bulk_delete(self, ids: list[int]) -> int:
        """Soft delete multiple violations by IDs."""
        if not ids:
            return 0

        statement = (
            update(ViolationModel)
            .where(ViolationModel.id.in_(ids), ViolationModel.is_deleted == False)  # noqa: E712
            .values(is_deleted=True, updated_at=get_current_utc7_time())
        )
        result = self.session.execute(statement)
        self.session.flush()
        return getattr(result, "rowcount", 0) or 0
