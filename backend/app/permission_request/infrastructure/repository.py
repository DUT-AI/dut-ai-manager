from typing import List, Optional

from app.permission_request.domain.entity import \
  PermissionRequest as DomainEntity
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.model import \
  PermissionRequest as ORMModel
from app.shared.infrastructure.base_repository import BaseRepository
from app.utils.datetime import get_current_utc7_time
from sqlalchemy import desc, extract, func
from sqlmodel import Session, select


class PermissionRequestRepository(BaseRepository[ORMModel]):
    """ORM-first (kế thừa BaseRepository); public API trả domain entity."""

    def __init__(self, session: Session):
        super().__init__(session, ORMModel)

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> List[DomainEntity]:
        stmt = (
            select(ORMModel)
            .where(ORMModel.is_deleted == deleted)
            .order_by(desc(ORMModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        rows = self.session.exec(stmt).all()
        return [r.to_entity() for r in rows]

    def get_by_month(
        self,
        month: int,
        year: int,
        limit: int = 1000,
        deleted: bool = False,
    ) -> List[DomainEntity]:
        stmt = (
            select(ORMModel)
            .where(
                ORMModel.is_deleted == deleted,
                extract("month", ORMModel.date) == month,
                extract("year", ORMModel.date) == year,
            )
            .order_by(desc(ORMModel.date))
            .limit(limit)
        )
        rows = self.session.exec(stmt).all()
        return [r.to_entity() for r in rows]

    def get_by_id(self, request_id: int) -> Optional[DomainEntity]:
        m = super().get_by_id(request_id)
        return m.to_entity() if m else None

    def get_by_user(
        self,
        user_id: int,
        month: Optional[int] = None,
        year: Optional[int] = None,
        deleted: bool = False,
    ) -> List[DomainEntity]:
        stmt = select(ORMModel).where(
            ORMModel.created_by == user_id, ORMModel.is_deleted == deleted
        )
        if month is not None:
            stmt = stmt.where(extract("month", ORMModel.date) == month)
        if year is not None:
            stmt = stmt.where(extract("year", ORMModel.date) == year)

        stmt = stmt.order_by(desc(ORMModel.date))
        rows = self.session.exec(stmt).all()
        return [r.to_entity() for r in rows]

    def count_by_user_category_month(
        self, user_id: int, category: RequestCategory, month: int, year: int
    ) -> int:
        stmt = select(func.count(ORMModel.id)).where(
            ORMModel.created_by == user_id,
            ORMModel.category == category,
            ORMModel.is_deleted == False,  # noqa: E712
            extract("month", ORMModel.date) == month,
            extract("year", ORMModel.date) == year,
        )
        return self.session.exec(stmt).one()

    def save(self, request: DomainEntity) -> DomainEntity:
        if request.id:
            orm = super().get_by_id(request.id)
            if orm:
                orm.category = request.category
                orm.date = request.date
                orm.note = request.reason
                orm.updated_at = get_current_utc7_time()
                self.update(orm)
                return orm.to_entity()

        model = ORMModel.from_entity(request)
        created = self.add(model)
        self.session.refresh(created)
        return created.to_entity()

    def delete(self, request_id: int) -> bool:
        orm = super().get_by_id(request_id)
        if orm:
            self.soft_delete(orm)
            return True
        return False

    def restore(self, request_id: int) -> bool:
        return super().restore(request_id) is not None
