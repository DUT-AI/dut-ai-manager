from datetime import date

from sqlalchemy import desc, extract, func, select
from sqlalchemy.orm import Session, joinedload

from app.meeting.infrastructure.model import Meeting
from app.permission_request.domain.entity import PermissionRequest as DomainEntity
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.model import PermissionRequest as ORMModel
from app.shared.domain.query_support import QuerySupport, apply_query_support
from app.shared.infrastructure.base_repository import BaseRepository


class PermissionRequestRepository(BaseRepository[ORMModel, DomainEntity]):
    """ORM-first (kế thừa BaseRepository); public API trả domain entity."""

    def __init__(self, session: Session):
        super().__init__(session, ORMModel)

    def get_all(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
    ) -> list[DomainEntity]:
        stmt = select(ORMModel).options(
            joinedload(ORMModel.user),
            joinedload(ORMModel.homework),
            joinedload(ORMModel.meeting),
        )

        if hasattr(ORMModel, "is_deleted"):
            stmt = stmt.where(ORMModel.is_deleted == deleted)

        if query_support:
            stmt = apply_query_support(stmt, ORMModel, query_support)
        else:
            # Default sorting if no query support provided
            stmt = stmt.order_by(desc(ORMModel.created_at))

        rows = self.session.scalars(stmt).unique().all()
        return [r.to_entity() for r in rows]

    def get_by_date(self, target_date: date) -> list[DomainEntity]:
        """Lấy tất cả yêu cầu xin phép trong một ngày cụ thể."""
        stmt = (
            select(ORMModel)
            .options(
                joinedload(ORMModel.user),
                joinedload(ORMModel.homework),
                joinedload(ORMModel.meeting),
            )
            .where(
                ORMModel.is_deleted.is_(False),
                func.date(ORMModel.created_at) == target_date,
            )
            .order_by(desc(ORMModel.created_at))
        )
        rows = self.session.scalars(stmt).unique().all()
        return [r.to_entity() for r in rows]

    def get_by_month(
        self,
        month: int,
        year: int,
        limit: int = 1000,
        deleted: bool = False,
    ) -> list[DomainEntity]:
        stmt = (
            select(ORMModel)
            .options(
                joinedload(ORMModel.user),
                joinedload(ORMModel.homework),
                joinedload(ORMModel.meeting),
            )
            .where(
                ORMModel.is_deleted == deleted,
                extract("month", ORMModel.created_at) == month,
                extract("year", ORMModel.created_at) == year,
            )
            .order_by(desc(ORMModel.created_at))
            .limit(limit)
        )
        rows = self.session.scalars(stmt).unique().all()
        return [r.to_entity() for r in rows]

    def get_by_user(
        self,
        user_id: int,
        month: int | None = None,
        year: int | None = None,
        deleted: bool = False,
    ) -> list[DomainEntity]:
        stmt = (
            select(ORMModel)
            .options(
                joinedload(ORMModel.user),
                joinedload(ORMModel.homework),
                joinedload(ORMModel.meeting),
            )
            .where(
                ORMModel.created_by == user_id,
                ORMModel.is_deleted == deleted,
            )
        )
        if month is not None:
            stmt = stmt.where(extract("month", ORMModel.created_at) == month)
        if year is not None:
            stmt = stmt.where(extract("year", ORMModel.created_at) == year)

        stmt = stmt.order_by(desc(ORMModel.created_at))
        rows = self.session.scalars(stmt).all()
        return [r.to_entity() for r in rows]

    def count_by_user_category_month(
        self, user_id: int, category: RequestCategory, month: int, year: int
    ) -> int:
        stmt = select(func.count(ORMModel.id)).where(
            ORMModel.created_by == user_id,
            ORMModel.category == category,
            ORMModel.is_deleted.is_(False),
            extract("month", ORMModel.created_at) == month,
            extract("year", ORMModel.created_at) == year,
        )
        return self.session.scalars(stmt).one()

    def has_postpone_request_for_date(self, user_id: int, target_date: date) -> bool:
        """Kiểm tra user có đơn xin tạm hoãn bài tập trong ngày không."""
        stmt = select(func.count(ORMModel.id)).where(
            ORMModel.created_by == user_id,
            ORMModel.category == RequestCategory.POSTPONE,
            ORMModel.is_deleted == False,
            func.date(ORMModel.created_at) == target_date,
        )
        return self.session.scalars(stmt).one() > 0

    def has_absence_request_for_date(self, user_id: int, target_date: date) -> bool:
        """Kiểm tra user có đơn xin vắng sinh hoạt trong ngày không."""
        stmt = select(func.count(ORMModel.id)).where(
            ORMModel.created_by == user_id,
            ORMModel.category == RequestCategory.ABSENCE,
            ORMModel.is_deleted.is_(False),
            func.date(ORMModel.created_at) == target_date,
        )
        return self.session.scalars(stmt).one() > 0

    def get_user_ids_with_requests_for_date(
        self, user_ids: list[int], target_date: date, category: RequestCategory
    ) -> set[int]:
        """Lấy danh sách các user_id đã có đơn xin phép theo loại và ngày cụ thể (Batch)."""
        if not user_ids:
            return set()

        stmt = (
            select(ORMModel.created_by)
            .join(Meeting, ORMModel.meeting_id == Meeting.id)
            .where(
                ORMModel.created_by.in_(user_ids),
                ORMModel.category == category,
                ORMModel.is_deleted == False,
                func.date(Meeting.start_time) == target_date,
            )
        )

        rows = self.session.scalars(stmt).unique().all()
        return {r for r in rows if r is not None}

    def get_postpone_requests_for_homeworks(
        self, homework_ids: list[int], user_ids: list[int]
    ) -> list[DomainEntity]:
        """Lấy danh sách đơn xin hoãn cho các bài tập và user cụ thể."""
        if not homework_ids or not user_ids:
            return []

        stmt = select(ORMModel).where(
            ORMModel.homework_id.in_(homework_ids),
            ORMModel.created_by.in_(user_ids),
            ORMModel.category == RequestCategory.POSTPONE,
            ORMModel.is_deleted.is_(False),
        )

        rows = self.session.scalars(stmt).unique().all()
        return [r.to_entity() for r in rows]

    def update(self, entity: DomainEntity) -> DomainEntity:
        return super().update(entity)

    def save(self, entity: DomainEntity) -> DomainEntity:
        if entity.id:
            return self.update(entity)
        return self.add(entity)

    def delete(self, request_id: int) -> bool:
        entity = self.get_by_id(request_id)
        if entity:
            self.soft_delete(entity)
            return True
        return False
