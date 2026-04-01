"""
Bonus Point Repository Interface and SQLite Implementation.
"""

from datetime import datetime
from typing import List, Optional

from app.bonus_point.domain.entity import BonusPoint
from app.bonus_point.infrastructure.model import BonusPointModel
from app.shared.infrastructure.base_repository import BaseRepository
from sqlalchemy import extract
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select


class BonusPointRepository(BaseRepository[BonusPointModel]):
    """SQLite implementation of the BonusPoint Repository."""

    def __init__(self, session: Session):
        super().__init__(session, BonusPointModel)

    def to_entity(self, model: Optional[BonusPointModel]) -> Optional[BonusPoint]:
        """Convert ORM model to Domain Entity."""
        if not model:
            return None
        return model.to_entity()

    def from_entity(self, entity: BonusPoint) -> BonusPointModel:
        """Convert Domain Entity to ORM model."""
        return BonusPointModel.from_entity(entity)

    def create(self, entity: BonusPoint) -> BonusPoint:
        model = self.from_entity(entity)
        created_model = self.add(model)
        return self.to_entity(created_model)  # type: ignore

    def get_by_entity_id(self, id: int) -> Optional[BonusPoint]:
        model = self.get_by_id(id)
        return self.to_entity(model)

    def get_all_entities(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> List[BonusPoint]:
        models = self.get_all(skip=skip, limit=limit, deleted=deleted)
        return [self.to_entity(model) for model in models]  # type: ignore

    def update_entity(self, entity: BonusPoint) -> BonusPoint:
        model = self.from_entity(entity)
        updated_model = self.update(model)
        return self.to_entity(updated_model)  # type: ignore

    def delete_entity(self, id: int) -> bool:
        model = self.get_by_id(id)
        if model:
            self.soft_delete(model)
            return True
        return False

    def restore_entity(self, id: int) -> Optional[BonusPoint]:
        model = self.restore(id)
        return self.to_entity(model)

    def to_entity(self, model: BonusPointModel) -> BonusPoint:
        """Convert ORM model to Domain Entity."""
        return model.to_entity()

    def from_entity(self, entity: BonusPoint) -> BonusPointModel:
        """Convert Domain Entity to ORM model."""
        return BonusPointModel.from_entity(entity)

    def get_by_user_id(
        self, user_id: int, month: Optional[int] = None, year: Optional[int] = None
    ) -> List[BonusPoint]:
        """Get all bonus points by a specific user, optionally filtered by month/year"""
        statement = select(BonusPointModel).where(
            BonusPointModel.is_deleted == False, BonusPointModel.user_id == user_id
        )

        if month is not None:
            statement = statement.where(
                extract("month", BonusPointModel.created_at) == month
            )
        if year is not None:
            statement = statement.where(
                extract("year", BonusPointModel.created_at) == year
            )

        statement = statement.options(
            joinedload(BonusPointModel.user),
        )
        statement.sort_by(BonusPointModel.created_at)

        models = list(self.session.exec(statement).all())
        return [self.to_entity(model) for model in models]

    def get_by_user_and_date(self, user_id: int, target_date) -> List[BonusPoint]:
        """Get bonus points for a user on a specific date"""

        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        statement = (
            select(BonusPointModel)
            .where(
                BonusPointModel.is_deleted == False,
                BonusPointModel.user_id == user_id,
                BonusPointModel.date >= start,
                BonusPointModel.date <= end,
            )
            .options(
                joinedload(BonusPointModel.user),
            )
            .sort_by(BonusPointModel.created_at)
        )
        models = list(self.session.exec(statement).all())
        return [self.to_entity(model) for model in models]

    def get_by_date(self, target_date) -> List[BonusPoint]:
        """Get all bonus points on a specific date"""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())

        statement = (
            select(BonusPointModel)
            .where(
                BonusPointModel.is_deleted == False,
                BonusPointModel.date >= start,
                BonusPointModel.date <= end,
            )
            .options(
                joinedload(BonusPointModel.user),
                joinedload(BonusPointModel.creator),
                joinedload(BonusPointModel.updater),
            )
        )
        models = list(self.session.exec(statement).all())
        return [self.to_entity(model) for model in models]

    def get_by_month(
        self, month: Optional[int], year: Optional[int], user_id: Optional[int] = None
    ) -> List[BonusPoint]:
        """Get all bonus points in a specific month"""
        statement = select(BonusPointModel).where(BonusPointModel.is_deleted == False)
        if user_id:
            statement = statement.where(BonusPointModel.user_id == user_id)
        if month:
            statement = statement.where(extract("month", BonusPointModel.date) == month)
        if year:
            statement = statement.where(extract("year", BonusPointModel.date) == year)

        statement = statement.options(
            joinedload(BonusPointModel.user),
            joinedload(BonusPointModel.creator),
            joinedload(BonusPointModel.updater),
        )
        models = list(self.session.exec(statement).all())
        return [self.to_entity(model) for model in models]
