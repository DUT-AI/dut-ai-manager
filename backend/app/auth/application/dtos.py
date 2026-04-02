from typing import Literal
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


class TokenPayloadResponse(BaseModel):
    """Token payload response schema"""

    sub: int
    name: str
    role: str = ""
    avatar: str = ""
    permissions: list[str] = []
    type: Literal["access", "refresh"] = "access"
    exp: int


class UserReponseMe(BaseModel):
    id: int
    is_deleted: bool
    name: str
    email: str
    status: str
    avatar_url: str
    role_name: str
    permissions: list[str]
