from typing import Any, Optional

from app.user.domain.entity import UserEntity, UserStatus
from pydantic import BaseModel, EmailStr, model_validator


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
    check_in_card_code: Optional[str] = None


class UserResponse(UserBase):
    """API: không trả về giá trị thật của check_in_card_code, chỉ cờ đã cấu hình."""

    id: int
    role_name: Optional[str] = None
    permissions: list[str] = []
    check_in_card_code_configured: bool = False

    @model_validator(mode="before")
    @classmethod
    def mask_check_in_card_code(cls, data: Any) -> Any:
        if isinstance(data, UserEntity):
            d = data.model_dump()
            has_code = bool((d.get("check_in_card_code") or "").strip())
            d.pop("check_in_card_code", None)
            d["check_in_card_code_configured"] = has_code
            return d
        if isinstance(data, dict):
            d = dict(data)
            if "check_in_card_code" in d:
                raw = d.get("check_in_card_code")
                has_code = bool((raw or "").strip()) if raw is not None else False
                d.pop("check_in_card_code", None)
                d["check_in_card_code_configured"] = d.get(
                    "check_in_card_code_configured", has_code
                )
            return d
        return data

    class Config:
        from_attributes = True


class UserSettingsUpdate(BaseModel):
    avatar_url: Optional[str] = None
    discord_id: Optional[str] = None
    check_in_card_code: Optional[str] = None


class UserImportResult(BaseModel):
    total: int
    success_count: int
    error_count: int
    errors: list[str] = []
