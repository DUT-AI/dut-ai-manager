from datetime import date, datetime
from typing import Optional

from app.permission_request.domain.value_objects import RequestCategory
from pydantic import BaseModel, ConfigDict


class PermissionRequestBase(BaseModel):
    category: RequestCategory
    date: date
    reason: str


class PermissionRequestCreate(PermissionRequestBase):
    pass


class PermissionRequestUpdate(BaseModel):
    category: Optional[RequestCategory] = None
    date: Optional[date] = None
    reason: Optional[str] = None


class PermissionRequestResponse(PermissionRequestBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
