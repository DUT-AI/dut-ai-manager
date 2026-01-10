from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""

    old_password: str
    new_password: str
    confirm_password: str


class UserResponse(BaseModel):
    """User response schema"""

    id: int
    name: str
    email: str
    phone_number: str | None = None
    status: str
    role_id: int | None = None
    role_name: str | None = None
    permissions: list[str] = []

    class Config:
        from_attributes = True
