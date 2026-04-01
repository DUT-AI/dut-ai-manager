from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt
from app.core.config import settings
from jwt.exceptions import PyJWTError
from loguru import logger
from passlib.context import CryptContext
from pydantic import (BaseModel, ConfigDict, Field, ValidationError,
                      field_validator)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


class TokenPayload(BaseModel):
    """Claims khi tạo access/refresh token (không có type — thêm lúc encode)."""

    sub: int
    name: str
    role: str = ""
    avatar: str = ""
    permissions: list[str] = Field(default_factory=list)


class AccessTokenPayload(BaseModel):
    """Payload sau khi giải mã access token."""

    model_config = ConfigDict(extra="ignore")

    sub: int
    type: Literal["access"]
    name: str = ""
    role: str = ""
    avatar: str = ""
    permissions: list[str] = Field(default_factory=list)

    @field_validator("sub", mode="before")
    @classmethod
    def coerce_sub(cls, v: Any) -> int:
        if v is None:
            raise ValueError("sub is required")
        return int(v)


class RefreshTokenPayload(BaseModel):
    """Payload sau khi giải mã refresh token (cho phép thừa claim từ access dump cũ)."""

    model_config = ConfigDict(extra="ignore")

    sub: int
    type: Literal["refresh"]
    name: str = ""
    role: str = ""
    avatar: str = ""
    permissions: list[str] = Field(default_factory=list)

    @field_validator("sub", mode="before")
    @classmethod
    def coerce_sub(cls, v: Any) -> int:
        if v is None:
            raise ValueError("sub is required")
        return int(v)


def create_access_token(
    subject: TokenPayload,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Tạo JWT access; exp là Unix timestamp (int)."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        exp_ts = int((now + expires_delta).timestamp())
    else:
        exp_ts = int(
            (now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
        )
    base = subject.model_dump(mode="json")
    base["sub"] = str(base["sub"])  # PyJWT yêu cầu sub là string (RFC)
    to_encode = {"exp": exp_ts, "type": "access", **base, **(extra_claims or {})}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    subject: TokenPayload, expires_delta: timedelta | None = None
) -> str:
    """Tạo JWT refresh; exp là Unix timestamp (int)."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        exp_ts = int((now + expires_delta).timestamp())
    else:
        exp_ts = int((now + timedelta(days=7)).timestamp())
    base = subject.model_dump(mode="json")
    base["sub"] = str(base["sub"])
    to_encode = {"exp": exp_ts, "type": "refresh", **base}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Giải mã JWT thành dict (tương thích auth_service / middleware).
    Lỗi chỉ log DEBUG, trả None.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError as e:
        logger.debug("decode_token (raw JWT) failed: {}", e)
        return None


def decode_access_token(token: str) -> AccessTokenPayload | None:
    try:
        raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return AccessTokenPayload.model_validate(raw)
    except (PyJWTError, ValidationError) as e:
        logger.debug("decode_access_token failed: {}", e)
        return None


def decode_refresh_token(token: str) -> RefreshTokenPayload | None:
    try:
        raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return RefreshTokenPayload.model_validate(raw)
    except (PyJWTError, ValidationError) as e:
        logger.debug("decode_refresh_token failed: {}", e)
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)
