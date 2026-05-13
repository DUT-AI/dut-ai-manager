from datetime import datetime
from typing import Optional

from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.value_objects import UserRef
from pydantic import Field


class BonusPoint(BaseEntity):
    """Bonus Point domain entity."""

    points: int
    reason: str = Field(max_length=500)
    date: datetime
    owner: Optional[UserRef] = None
    creator: Optional[UserRef] = None
    updater: Optional[UserRef] = None
