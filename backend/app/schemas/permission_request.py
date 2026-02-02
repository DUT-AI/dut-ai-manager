from datetime import datetime, date as dt_date, time as dt_time
from typing import Optional

from app.models.permission_request import RequestCategory
from pydantic import BaseModel


class PermissionRequestBase(BaseModel):
    category: RequestCategory
    note: str
    date: dt_date
    start_time: dt_time
    end_time: dt_time


class PermissionRequestCreate(PermissionRequestBase):
    pass


class PermissionRequestUpdate(BaseModel):
    category: Optional[RequestCategory] = None
    note: Optional[str] = None
    date: Optional[dt_date] = None
    start_time: Optional[dt_time] = None
    end_time: Optional[dt_time] = None


class PermissionRequestResponse(PermissionRequestBase):
    id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None  # Alias for creator's name
    user_avatar: Optional[str] = None
    creator_name: Optional[str] = None
    updater_name: Optional[str] = None
    is_deleted: bool

    class Config:
        from_attributes = True
