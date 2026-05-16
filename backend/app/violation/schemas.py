"""
Violation Schemas — Pydantic DTOs for request/response.

These are separate from Domain Entities. Schemas are for API serialization.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.shared.domain.value_objects import UserRef

# --- Request DTOs ---


class ViolationCreate(BaseModel):
    """Request body for creating violations."""

    reason: str
    date: datetime
    user_ids: list[int]


class ViolationUpdate(BaseModel):
    """Request body for updating a violation."""

    reason: str | None = None
    date: datetime | None = None


# --- Response DTOs ---


class ViolationResponse(BaseModel):
    """Response DTO for a violation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reason: str
    date: datetime
    user_id: int
    created_by: int | None = None
    updated_by: int | None = None
    created_at: datetime
    updated_at: datetime

    # Embedded user refs (Standardized)
    owner: UserRef | None = None
    creator: UserRef | None = None
    updater: UserRef | None = None
