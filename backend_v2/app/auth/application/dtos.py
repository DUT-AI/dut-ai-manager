from pydantic import BaseModel, EmailStr


class LoginRequestDTO(BaseModel):
    email: EmailStr
    password: str


class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str


class RefreshTokenRequestDTO(BaseModel):
    refresh_token: str


class ChangePasswordRequestDTO(BaseModel):
    old_password: str
    new_password: str


class UserAuthContextDTO(BaseModel):
    id: int
    email: str
    hashed_password: str
    is_active: bool
    name: str = ""
    avatar_url: str = ""
    role_name: str | None = None
    permissions: list[str] = []


class CurrentUserDTO(BaseModel):
    id: int
    email: str
    name: str = ""
    avatar_url: str = ""
    role_name: str | None = None
    permissions: list[str] = []
