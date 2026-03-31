"""
Violation Repository — data access layer.

Uses flush() instead of commit(). Session commits at middleware level.
Mapping delegated to ViolationModel.to_entity() / .from_entity().
"""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import desc, extract
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select

from app.violation.domain.entity import Violation
from app.violation.infrastructure.model import ViolationModel


class ViolationRepository:
    """Concrete repository — no interface needed."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, entity: Violation) -> Violation:
        """Create a new violation and return fully loaded entity."""
        model = ViolationModel.from_entity(entity)
        self.session.add(model)
        self.session.flush()
        
        # Refresh to get ID and also load relationships for the entity
        statement = select(ViolationModel).where(ViolationModel.id == model.id).options(
            joinedload(ViolationModel.user),
            joinedload(ViolationModel.creator_rel),
            joinedload(ViolationModel.updater_rel),
        )
        model = self.session.exec(statement).first()
        
        logger.debug(f"Saved violation: id={model.id}")
        return model.to_entity()

    def get_by_id(self, item_id: int) -> Optional[Violation]:
        """Get violation by ID with user details."""
        statement = (
            select(ViolationModel)
            .where(ViolationModel.id == item_id, ViolationModel.is_deleted == False)
            .options(
                joinedload(ViolationModel.user),
                joinedload(ViolationModel.creator_rel),
                joinedload(ViolationModel.updater_rel),
            )
        )
        model = self.session.exec(statement).first()
        if not model:
            return None
        return model.to_entity()

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> list[Violation]:
        """Get all violations with user details."""
        statement = (
            select(ViolationModel)
            .where(ViolationModel.is_deleted == deleted)
            .options(
                joinedload(ViolationModel.user),
                joinedload(ViolationModel.creator_rel),
                joinedload(ViolationModel.updater_rel),
            )
            .order_by(desc(ViolationModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        return [m.to_entity() for m in self.session.exec(statement).all()]

    def get_by_month(
        self, month: int, year: int, user_id: Optional[int] = None
    ) -> list[Violation]:
        """Get violations filtered by month/year."""
        statement = select(ViolationModel).where(ViolationModel.is_deleted == False)
        if user_id:
            statement = statement.where(ViolationModel.user_id == user_id)
        if month:
            statement = statement.where(
                extract("month", ViolationModel.date) == month
            )
        if year:
            statement = statement.where(
                extract("year", ViolationModel.date) == year
            )
        statement = statement.options(
            joinedload(ViolationModel.user),
            joinedload(ViolationModel.creator_rel),
            joinedload(ViolationModel.updater_rel),
        )
        return [m.to_entity() for m in self.session.exec(statement).all()]

    def get_by_user_and_date(
        self, user_id: int, target_date: datetime
    ) -> list[Violation]:
        """Get violations for a user on a specific date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        statement = (
            select(ViolationModel)
            .where(
                ViolationModel.is_deleted == False,
                ViolationModel.user_id == user_id,
                ViolationModel.date >= start,
                ViolationModel.date <= end,
            )
            .options(
                joinedload(ViolationModel.user),
                joinedload(ViolationModel.creator_rel),
                joinedload(ViolationModel.updater_rel),
            )
        )
        return [m.to_entity() for m in self.session.exec(statement).all()]

    def get_by_date(self, target_date: datetime) -> list[Violation]:
        """Get all violations on a specific date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        statement = (
            select(ViolationModel)
            .where(
                ViolationModel.is_deleted == False,
                ViolationModel.date >= start,
                ViolationModel.date <= end,
            )
            .options(
                joinedload(ViolationModel.user),
                joinedload(ViolationModel.creator_rel),
                joinedload(ViolationModel.updater_rel),
            )
        )
        return [m.to_entity() for m in self.session.exec(statement).all()]

    def update(self, entity: Violation) -> Optional[Violation]:
        """Update an existing violation."""
        model = self.session.get(ViolationModel, entity.id)
        if not model:
            return None
        model.reason = entity.reason
        model.date = entity.date
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return model.to_entity()

    def soft_delete(self, item_id: int) -> bool:
        """Soft delete a violation."""
        model = self.session.get(ViolationModel, item_id)
        if not model:
            return False
        model.is_deleted = True
        self.session.add(model)
        self.session.flush()
        return True

    def restore(self, item_id: int) -> Optional[Violation]:
        """Restore a soft-deleted violation."""
        statement = select(ViolationModel).where(
            ViolationModel.id == item_id, ViolationModel.is_deleted == True
        )
        model = self.session.exec(statement).first()
        if not model:
            return None
        model.is_deleted = False
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return model.to_entity()

