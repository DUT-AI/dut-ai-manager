"""
Violation Schemas — Pydantic DTOs for request/response.

These are separate from Domain Entities. Schemas are for API serialization.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

# --- Shared nested DTOs ---


class UserRefResponse(BaseModel):
    """Nested user info in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = ""
    avatar: str | None = None


# --- Request DTOs ---


class ViolationCreate(BaseModel):
    """Request body for creating violations."""

    reason: str
    date: datetime
    user_ids: list[int]


class ViolationUpdate(BaseModel):
    """Request body for updating a violation."""

    reason: Optional[str] = None
    date: Optional[datetime] = None


# --- Response DTOs ---


class ViolationResponse(BaseModel):
    """Response DTO for a violation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reason: str
    date: datetime
    user_id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Embedded user refs
    owner: UserRefResponse | None = None
    creator: UserRefResponse | None = None
    updater: UserRefResponse | None = None
