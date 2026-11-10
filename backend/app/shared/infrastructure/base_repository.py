"""
Base repository for new domain-driven modules.

Key features:
    - Uses flush() instead of commit() — session commits at middleware level
    - Works with ORM Models internally, maps to Domain Entities for callers
    - Supports both integer and RFC 9562 UUIDv7 primary keys
    - Automatically checks if model supports soft-deletion (is_deleted)
    - Separates soft_delete() and hard_delete() operations
"""

from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.shared.domain.query_support import (
    QuerySupport,
    apply_filters_only,
    apply_query_support,
)

# TypeVar definitions for Model and Entity
TModel = TypeVar("TModel", bound=Any)
TEntity = TypeVar("TEntity", bound=Any)


class BaseRepository[TModel: Any, TEntity: Any]:
    """Base repository — uses flush() for atomicity, NOT commit()."""

    def __init__(self, session: Session, model: type[TModel]):
        self.session = session
        self.model = model

    def _normalize_id(self, id_val: Any) -> Any:
        """Convert string UUID to UUID object if possible to avoid dialect type errors."""
        if isinstance(id_val, str):
            try:
                return UUID(id_val)
            except ValueError:
                return id_val
        return id_val

    def add(self, entity: TEntity) -> TEntity:
        """Add an entity to session and flush."""
        model = self.model.from_entity(entity)
        self.session.add(model)
        self.session.flush()
        return cast(TEntity, model.to_entity())

    def get_by_id(self, id: int | UUID | str) -> TEntity | None:
        """Get model by ID (int or UUID), returns None if soft-deleted."""
        normalized_id = self._normalize_id(id)
        model = self.session.get(self.model, normalized_id)
        if model and getattr(model, "is_deleted", False):
            return None
        return cast(TEntity, model.to_entity()) if model else None

    def get_one(
        self,
        query_support: QuerySupport,
        deleted: bool = False,
    ) -> TEntity | None:
        """Get a single model using query support (filtering, relations)."""
        query = select(self.model)
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted == deleted)
        query = apply_query_support(query, self.model, query_support)

        # Get first result
        orm = self.session.scalars(query).unique().first()
        return cast(TEntity, orm.to_entity()) if orm else None

    def get_all(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
    ) -> list[TEntity]:
        """Get all models with query support (filtering, sorting, pagination)."""
        query = select(self.model)
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted == deleted)

        if query_support:
            query = apply_query_support(query, self.model, query_support)

        orms = self.session.scalars(query).unique().all()
        return [cast(TEntity, m.to_entity()) for m in orms]

    def get_paged(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
    ) -> tuple[list[TEntity], int]:
        """Get paginated models and total count with optimized COUNT query."""
        # 1. Optimized Count Query: Filter only, no sorting or eager joins
        count_stmt = select(func.count(self.model.id))
        if hasattr(self.model, "is_deleted"):
            count_stmt = count_stmt.where(self.model.is_deleted == deleted)

        if query_support and query_support.filters:
            count_stmt = apply_filters_only(
                count_stmt, self.model, query_support.filters
            )
        total = self.session.scalar(count_stmt) or 0

        # 2. Select Query: Full query support (include, filter, sorting, pagination)
        query = select(self.model)
        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted == deleted)

        if query_support:
            query = apply_query_support(query, self.model, query_support)

        orms = self.session.scalars(query).unique().all()
        return [cast(TEntity, m.to_entity()) for m in orms], total

    def update(self, entity: TEntity) -> TEntity:
        """Update a model (merge into session and flush)."""
        model = self.model.from_entity(entity)

        # Fix for default_factory overwriting audit fields on new model instance creation
        if (
            hasattr(entity, "created_at")
            and entity.created_at
            and hasattr(model, "created_at")
        ):
            model.created_at = entity.created_at
        if (
            hasattr(entity, "created_by")
            and entity.created_by
            and hasattr(model, "created_by")
        ):
            model.created_by = entity.created_by

        attached_model = self.session.merge(model)
        self.session.flush()
        return cast(TEntity, attached_model.to_entity())

    def soft_delete(self, entity_or_id: TEntity | int | UUID | str) -> None:
        """
        Soft delete a model.
        Raises NotImplementedError if model does not support is_deleted.
        """
        if not hasattr(self.model, "is_deleted"):
            raise NotImplementedError(
                f"Model {self.model.__name__} does not support soft delete"
            )

        target_id = self._normalize_id(getattr(entity_or_id, "id", entity_or_id))
        model = self.session.get(self.model, target_id)
        if model:
            model.is_deleted = True
            self.session.add(model)
            self.session.flush()

    def delete_by_id(self, id: int | UUID | str) -> bool:
        """
        Soft delete a model by ID.
        Raises NotImplementedError if model does not support is_deleted.
        """
        if not hasattr(self.model, "is_deleted"):
            raise NotImplementedError(
                f"Model {self.model.__name__} does not support soft delete"
            )

        normalized_id = self._normalize_id(id)
        model = self.session.get(self.model, normalized_id)
        if not model:
            return False

        model.is_deleted = True
        self.session.add(model)
        self.session.flush()
        return True

    def hard_delete(self, entity_or_id: TEntity | int | UUID | str) -> None:
        """Permanently delete a model from database."""
        target_id = self._normalize_id(getattr(entity_or_id, "id", entity_or_id))
        model = self.session.get(self.model, target_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def hard_delete_by_id(self, id: int | UUID | str) -> bool:
        """Permanently delete a model by ID from database."""
        normalized_id = self._normalize_id(id)
        model = self.session.get(self.model, normalized_id)
        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def restore(self, entity: TEntity) -> TEntity:
        """Restore a soft-deleted model."""
        if not hasattr(self.model, "is_deleted") or not getattr(entity, "id", None):
            raise NotImplementedError(
                f"Model {self.model.__name__} does not support soft delete or ID is missing"
            )

        model_id = entity.id
        statement = select(self.model).where(
            cast(Any, self.model).id == model_id,
            cast(Any, self.model).is_deleted == True,  # noqa: E712
        )
        model = self.session.scalars(statement).first()

        if not model:
            raise ValueError(f"Failed to find soft-deleted model with id {model_id}")

        model.is_deleted = False
        self.session.add(model)
        self.session.flush()
        return cast(TEntity, model.to_entity())

    def flush(self) -> None:
        """Explicitly flush session to database."""
        self.session.flush()
