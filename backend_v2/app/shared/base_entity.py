from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseEntity(BaseModel):
    """Base class for domain entities."""

    id: int | None = None
    is_deleted: bool = False
    created_at: datetime | None = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
