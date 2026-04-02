from typing import List, Optional, Any, cast

from app.permission_request.domain.entity import \
  PermissionRequest as DomainEntity
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.model import \
  PermissionRequest as ORMModel
from app.shared.infrastructure.base_repository import BaseRepository
from sqlalchemy import desc, extract, func
from sqlmodel import Session, select
from app.shared.domain.query_support import QuerySupport, apply_query_support


class PermissionRequestRepository(BaseRepository[ORMModel, DomainEntity]):
    """ORM-first (kế thừa BaseRepository); public API trả domain entity."""

    def __init__(self, session: Session):
        super().__init__(session, ORMModel)

    def get_all(
        self,
        query_support: Optional[QuerySupport] = None,
        deleted: bool = False,
    ) -> List[DomainEntity]:
        stmt = select(ORMModel)
        
        if hasattr(ORMModel, "is_deleted"):
            stmt = stmt.where(cast(Any, ORMModel.is_deleted) == deleted)

        if query_support:
            stmt = apply_query_support(stmt, ORMModel, query_support)
        else:
            # Default sorting if no query support provided
            stmt = stmt.order_by(desc(cast(Any, ORMModel.created_at)))
            
        rows = self.session.exec(stmt).unique().all()
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
                getattr(ORMModel, "is_deleted") == deleted,
                extract("month", cast(Any, ORMModel.date)) == month,
                extract("year", cast(Any, ORMModel.date)) == year,
            )
            .order_by(desc(cast(Any, ORMModel.date)))
            .limit(limit)
        )
        rows = self.session.exec(stmt).all()
        return [r.to_entity() for r in rows]

    def get_by_user(
        self,
        user_id: int,
        month: Optional[int] = None,
        year: Optional[int] = None,
        deleted: bool = False,
    ) -> List[DomainEntity]:
        stmt = select(ORMModel).where(
            ORMModel.created_by == user_id, getattr(ORMModel, "is_deleted") == deleted
        )
        if month is not None:
            stmt = stmt.where(extract("month", cast(Any, ORMModel.date)) == month)
        if year is not None:
            stmt = stmt.where(extract("year", cast(Any, ORMModel.date)) == year)

        stmt = stmt.order_by(desc(cast(Any, ORMModel.date)))
        rows = self.session.exec(stmt).all()
        return [r.to_entity() for r in rows]

    def count_by_user_category_month(
        self, user_id: int, category: RequestCategory, month: int, year: int
    ) -> int:
        stmt = select(func.count(ORMModel.id)).where(
            ORMModel.created_by == user_id,
            ORMModel.category == category,
            getattr(ORMModel, "is_deleted") == False,  # noqa: E712
            extract("month", cast(Any, ORMModel.date)) == month,
            extract("year", cast(Any, ORMModel.date)) == year,
        )
        return self.session.exec(stmt).one()

    def update(self, entity: DomainEntity) -> Optional[DomainEntity]:
        return super().update(entity)

    def save(self, entity: DomainEntity) -> Optional[DomainEntity]:
        if entity.id:
            return self.update(entity)
        return self.add(entity)

    def delete(self, request_id: int) -> bool:
        entity = self.get_by_id(request_id)
        if entity:
            self.soft_delete(entity)
            return True
        return False

    def restore(self, entity: DomainEntity) -> Optional[DomainEntity]:
        return super().restore(entity)
