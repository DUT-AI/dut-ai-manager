from datetime import datetime

from pydantic import BaseModel

from app.bonus_point.domain.value_objects import BonusPointType
from app.shared.domain.value_objects import UserRef


class BonusPointBase(BaseModel):
    points: int
    reason: str
    date: datetime
    type: BonusPointType | None = None


class BonusPointCreate(BonusPointBase):
    user_ids: list[int]


class BonusPointUpdate(BaseModel):
    points: int | None = None
    reason: str | None = None
    date: datetime | None = None
    type: BonusPointType | None = None


class BonusPointResponse(BonusPointBase):
    id: int
    user_id: int
    type: BonusPointType = BonusPointType.OTHER
    owner: UserRef | None = None
    creator: UserRef | None = None
    updater: UserRef | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
