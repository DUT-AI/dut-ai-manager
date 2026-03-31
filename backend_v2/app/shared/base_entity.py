from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseEntity(BaseModel):
    """Base class for domain entities."""

    id: int | None = None
    is_deleted: bool = False
    created_at: datetime | None = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default_factory=datetime.utcnow)
    created_by: int | None = None
    updated_by: int | None = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

