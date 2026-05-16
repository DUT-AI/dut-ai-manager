"""
Base repository for new domain-driven modules.

Key differences from the old BaseRepository (api/v1/repositories/base.py):
    - Uses flush() instead of commit() — session commits at middleware level
    - Works with ORM Models internally, maps to Domain Entities for callers
    - Subclasses should use Entity.model_validate(model) for mapping

Old modules can keep using the old BaseRepository until they are migrated.
"""

from typing import Generic, TypeVar, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.query_support import QuerySupport, apply_query_support
from app.shared.infrastructure.base_model import SQLAlchemyTimestampMixin

# Định nghĩa TypeVar cho Model và Entity
TModel = TypeVar("TModel", bound=SQLAlchemyTimestampMixin)

TEntity = TypeVar("TEntity", bound=BaseEntity)


class BaseRepository(Generic[TModel, TEntity]):
    """Base repository — uses flush() for atomicity, NOT commit()."""

    def __init__(self, session: Session, model: type[TModel]):
        self.session = session
        self.model = model

    def add(self, entity: TEntity) -> TEntity:
        """Add an entity to session and flush."""
        model = self.model.from_entity(entity)
        self.session.add(model)
        self.session.flush()
        return cast(TEntity, model.to_entity())

    def get_by_id(self, id: int) -> TEntity | None:
        """Get model by ID, returns None if soft-deleted."""
        model = self.session.get(self.model, id)
        if model and getattr(model, "is_deleted", False):
            return None
        return cast(TEntity, model.to_entity()) if model else None

    def get_one(
        self,
        query_support: QuerySupport,
        deleted: bool = False,
    ) -> TEntity | None:
        """Get a single model using query support (filtering, relations)."""
        query = select(self.model).where(self.model.is_deleted == deleted)
        query = apply_query_support(query, self.model, query_support)

        # Get first result
        orm = self.session.scalars(query).unique().first()
        return cast(TEntity, orm.to_entity()) if orm else None

    def get_all(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
    ) -> list[TEntity]:
        """Get all models with  query support (filtering, sorting, pagination)."""
        query = select(self.model).where(self.model.is_deleted == deleted)

        if query_support:
            query = apply_query_support(query, self.model, query_support)

        orms = self.session.scalars(query).unique().all()
        return [cast(TEntity, m.to_entity()) for m in orms]

    def update(self, entity: TEntity) -> TEntity:
        """Update a model (merge into session and flush)."""
        model = self.model.from_entity(entity)

        # Fix for default_factory overwriting audit fields on new model instance creation
        if entity.created_at:
            model.created_at = entity.created_at
        if entity.created_by:
            model.created_by = entity.created_by

        attached_model = self.session.merge(model)
        self.session.flush()
        return cast(TEntity, attached_model.to_entity())

    def soft_delete(self, entity: TEntity) -> None:
        """Soft delete a model."""
        model = self.session.get(self.model, entity.id)
        if model:
            model.is_deleted = True
            self.session.add(model)
            self.session.flush()

    def delete_by_id(self, id: int) -> bool:
        """Soft delete a model by ID."""
        model = self.session.get(self.model, id)
        if not model:
            return False

        model.is_deleted = True
        self.session.add(model)

        self.session.flush()
        return True

    def hard_delete(self, entity: TEntity) -> None:
        """Permanently delete a model."""
        model = self.session.get(self.model, entity.id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def restore(self, entity: TEntity) -> TEntity:
        """Restore a soft-deleted model."""
        if not hasattr(self.model, "is_deleted") or not entity.id:
            raise Exception(
                f"Model {self.model.__name__} does not support soft delete or ID is missing"
            )

        model_id = entity.id
        statement = select(self.model).where(
            self.model.id == model_id,
            self.model.is_deleted == True,
        )
        model = self.session.scalars(statement).first()

        if not model:
            raise Exception(f"Failed to find soft-deleted model with id {model_id}")

        model.is_deleted = False
        self.session.add(model)
        self.session.flush()
        return cast(TEntity, model.to_entity())

    def flush(self) -> None:
        """Explicitly flush session to database."""
        self.session.flush()
