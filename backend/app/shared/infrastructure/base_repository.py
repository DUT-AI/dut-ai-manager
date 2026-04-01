"""
Base repository for new domain-driven modules.

Key differences from the old BaseRepository (api/v1/repositories/base.py):
    - Uses flush() instead of commit() — session commits at middleware level
    - Works with ORM Models internally, maps to Domain Entities for callers
    - Subclasses should use Entity.model_validate(model) for mapping

Old modules can keep using the old BaseRepository until they are migrated.
"""

from typing import Generic, Optional, Type, TypeVar

from sqlmodel import Session, SQLModel, select

TModel = TypeVar("TModel", bound=SQLModel)


class BaseRepository(Generic[TModel]):
    """Base repository — uses flush() for atomicity, NOT commit()."""

    def __init__(self, session: Session, model: Type[TModel]):
        self.session = session
        self.model = model

    def add(self, model: TModel) -> TModel:
        """Add a model to session and flush to get ID."""
        self.session.add(model)
        self.session.flush()
        return model

    def get_by_id(self, id: int) -> Optional[TModel]:
        """Get model by ID, returns None if soft-deleted."""
        entity = self.session.get(self.model, id)
        if entity and getattr(entity, "is_deleted", False):
            return None
        return entity

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        deleted: bool = False,
        user_id: int | None = None,
    ) -> list[TModel]:
        """Get all models with optional user_id filter and pagination."""
        query = select(self.model)
        if user_id:
            query = query.where(getattr(self.model, "user_id") == user_id)
        if deleted:
            query = query.where(getattr(self.model, "is_deleted", False) == deleted)
        query = query.offset(skip).limit(limit)
        return list(self.session.exec(query).all())

    def update(self, model: TModel) -> TModel:
        """Update a model (add to session and flush)."""
        self.session.add(model)
        self.session.flush()
        return model

    def soft_delete(self, model: TModel) -> None:
        """Soft delete a model."""
        if hasattr(model, "is_deleted"):
            model.is_deleted = True
            self.session.add(model)
        else:
            self.session.delete(model)
        self.session.flush()

    def hard_delete(self, model: TModel) -> None:
        """Permanently delete a model."""
        self.session.delete(model)
        self.session.flush()

    def restore(self, id: int) -> Optional[TModel]:
        """Restore a soft-deleted model."""
        if not hasattr(self.model, "is_deleted"):
            return None

        statement = select(self.model).where(
            self.model.id == id, self.model.is_deleted == True  # noqa: E712
        )
        entity = self.session.exec(statement).first()

        if entity:
            entity.is_deleted = False
            self.session.add(entity)
            self.session.flush()
            return entity
        return None
