from typing import List, Optional

from app.user.domain.user_entity import UserStatus
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBaseDTO(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    role_id: Optional[int] = None
    avatar_url: Optional[str] = None
    discord_id: Optional[str] = None


class UserCreateDTO(UserBaseDTO):
    pass


class UserUpdateDTO(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    status: Optional[UserStatus] = None
    role_id: Optional[int] = None
    avatar_url: Optional[str] = None
    discord_id: Optional[str] = None


class UserResponseDTO(UserBaseDTO):
    id: int
    role_name: Optional[str] = None
    permissions: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class UserSettingsUpdateDTO(BaseModel):
    avatar_url: Optional[str] = None
    discord_id: Optional[str] = None


class UserImportResultDTO(BaseModel):
    total: int
    success_count: int
    error_count: int
    errors: List[str] = []
