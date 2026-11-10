"""
Base domain entity using Pydantic BaseModel.

Domain entities are PURE — they must NOT import from infrastructure layers
(sqlmodel, sqlalchemy, fastapi, etc.).

Supports:
- BaseGenericEntity[TId]: Generic ID entity with UTC timestamps (no soft-delete).
- BaseUuidEntity: Specialized entity with RFC 9562 UUIDv7 primary key (no soft-delete).
- SoftDeleteEntityMixin: Opt-in mixin for soft-delete support (`is_deleted: bool`).
- AuditEntityMixin: Opt-in mixin for user auditing (`created_by`, `updated_by`).
- BaseEntity: Backward-compatible base entity (int ID, audit fields, soft-delete).
"""

from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.shared.domain.uuid_utils import uuid7

TId = TypeVar("TId")


class BaseGenericEntity(BaseModel, Generic[TId]):
    """Base domain entity with generic primary key and UTC timestamps."""

    model_config = ConfigDict(from_attributes=True)

    id: TId | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SoftDeleteEntityMixin(BaseModel):
    """Opt-in mixin adding soft-delete support for domain entities."""

    is_deleted: bool = False


class AuditEntityMixin(BaseModel):
    """Opt-in mixin adding audit user IDs for domain entities."""

    created_by: int | None = None
    updated_by: int | None = None


class BaseUuidEntity(BaseGenericEntity[UUID]):
    """Base domain entity with RFC 9562 UUIDv7 primary key."""

    id: UUID = Field(default_factory=uuid7)


class BaseAuditEntity(BaseGenericEntity[int], AuditEntityMixin):
    """
    Base domain entity with integer ID and audit fields WITHOUT soft-delete.
    Used for entities that support pure physical hard-delete.
    """

    pass


class BaseEntity(BaseGenericEntity[int], AuditEntityMixin, SoftDeleteEntityMixin):
    """
    Legacy base entity for integer IDs with audit fields and soft-delete.
    Maintains 100% backward compatibility for all existing domain entities.
    """

    model_config = ConfigDict(from_attributes=True)
