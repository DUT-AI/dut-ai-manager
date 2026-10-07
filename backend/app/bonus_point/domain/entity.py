from datetime import datetime

from pydantic import Field

from app.bonus_point.domain.value_objects import BonusPointType
from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.value_objects import UserRef


class BonusPoint(BaseEntity):
    """Bonus Point domain entity."""

    points: int
    reason: str = Field(max_length=500)
    date: datetime
    type: BonusPointType = BonusPointType.OTHER
    user_id: int | None = None
    owner: UserRef | None = None
    creator: UserRef | None = None
    updater: UserRef | None = None
