from datetime import datetime

from pydantic import BaseModel

from app.shared.domain.value_objects import UserRef


class ViolationBase(BaseModel):
    reason: str
    date: datetime


class ViolationCreate(ViolationBase):
    user_ids: list[int]


class ViolationUpdate(BaseModel):
    reason: str | None = None
    date: datetime | None = None


class ViolationResponse(ViolationBase):
    id: int
    user_id: int
    owner: UserRef | None = None
    creator: UserRef | None = None
    updater: UserRef | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
