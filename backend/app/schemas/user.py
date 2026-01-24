from typing import Optional

from app.models.user import UserStatus
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    role_id: Optional[int] = None
    avatar_url: Optional[str] = None
    discord_id: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    status: Optional[UserStatus] = None
    role_id: Optional[int] = None
    avatar_url: Optional[str] = None
    discord_id: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role_name: Optional[str] = None

    class Config:
        from_attributes = True


class UserSettingsUpdate(BaseModel):
    avatar_url: Optional[str] = None
    discord_id: Optional[str] = None
