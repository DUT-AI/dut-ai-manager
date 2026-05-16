from typing import Any

from pydantic import BaseModel, EmailStr, model_validator

from app.user.domain.entity import UserEntity, UserStatus


class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone_number: str | None = None
    status: UserStatus = UserStatus.ACTIVE
    role_id: int | None = None
    avatar_url: str | None = None
    discord_id: str | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    role_id: int | None = None
    status: UserStatus | None = None
    avatar_url: str | None = None
    discord_id: str | None = None
    check_in_card_code: str | None = None


class UserResponse(UserBase):
    """API: không trả về giá trị thật của check_in_card_code, chỉ cờ đã cấu hình."""

    id: int
    role_name: str | None = None
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
    avatar_url: str | None = None
    discord_id: str | None = None
    check_in_card_code: str | None = None


class UserImportResult(BaseModel):
    total: int
    success_count: int
    error_count: int
    errors: list[str] = []
