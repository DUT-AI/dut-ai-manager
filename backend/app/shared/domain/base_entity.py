"""
Base domain entity using Pydantic BaseModel.

All domain entities should inherit from this class.
Domain entities are PURE — they must NOT import from infrastructure layers
(sqlmodel, sqlalchemy, fastapi, etc.).

Use `from_attributes=True` to enable mapping from ORM models:
    entity = MyEntity.model_validate(orm_model)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseEntity(BaseModel):
    """Base domain entity — Pydantic BaseModel, NO ORM dependency."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: int | None = None
    updated_by: int | None = None
    is_deleted: bool = False
