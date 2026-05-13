from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.shared.domain.value_objects import UserRef


class BonusPointBase(BaseModel):
    points: int
    reason: str
    date: datetime


class BonusPointCreate(BonusPointBase):
    user_ids: List[int]


class BonusPointUpdate(BaseModel):
    points: Optional[int] = None
    reason: Optional[str] = None
    date: Optional[datetime] = None


class BonusPointResponse(BonusPointBase):
    id: int
    user_id: int
    owner: Optional[UserRef] = None
    creator: Optional[UserRef] = None
    updater: Optional[UserRef] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
