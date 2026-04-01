from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ViolationBase(BaseModel):
    reason: str
    date: datetime


class ViolationCreate(ViolationBase):
    user_ids: List[int]


class ViolationUpdate(BaseModel):
    reason: Optional[str] = None
    date: Optional[datetime] = None


class ViolationResponse(ViolationBase):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    creator_name: Optional[str] = None
    updater_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
