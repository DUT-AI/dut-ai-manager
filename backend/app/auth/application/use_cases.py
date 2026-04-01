"""
Auth Application Use Cases — business logic layer.
"""

import random
import string
from datetime import timedelta
from typing import Optional, Tuple

from app.auth.domain.entity import Account
from app.auth.infrastructure.repository import AccountRepository
from app.core.config import settings
from app.user.domain.entity import UserEntity, UserStatus
from app.user.infrastructure.repository import UserRepository
from app.utils.password import (TokenPayload, create_access_token, create_refresh_token,
                                decode_access_token, decode_refresh_token,
                                get_password_hash, hash_password, verify_password)
from fastapi import HTTPException
from loguru import logger


class BaseAuthUseCase:
    """Base logic for auth operations."""

    def __init__(self, account_repo: AccountRepository, user_repo: UserRepository):
        self.account_repo = account_repo
        self.user_repo = user_repo

    def create_tokens(self, user: UserEntity) -> Tuple[str, str]:
        """Create access and refresh tokens for user."""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        subject = TokenPayload(
            sub=user.id,
            name=user.name,
            role=user.role_name or "",
            avatar=user.avatar_url or "",
            permissions=sorted(user.permissions),
        )
        access_token = create_access_token(
            subject=subject,
            expires_delta=access_token_expires,
        )
        refresh_token = create_refresh_token(subject=subject)
        return access_token, refresh_token


class AuthenticateUseCase(BaseAuthUseCase):
    """Authenticate and issue tokens."""

    def execute(self, email: str, password: str) -> Tuple[UserEntity, str, str]:
        user = self.user_repo.get_by_email(email)
        if not user or not user.account_id:
            raise HTTPException(
                status_code=400, detail="User not found or has no account"
            )

        if user.status == UserStatus.INACTIVE:
            raise HTTPException(status_code=400, detail="Account is inactive")

        account = self.account_repo.get_by_id(user.account_id)
        if not account or not verify_password(password, account.hash_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        access_token, refresh_token = self.create_tokens(user)
        logger.info(f"User {user.id} logged in.")
        return user, access_token, refresh_token


class RefreshTokenUseCase(BaseAuthUseCase):
    """Issue new tokens given a valid refresh token."""

    def execute(self, refresh_token_str: str) -> Tuple[str, str]:
        payload = decode_refresh_token(refresh_token_str)
        if not payload:
            raise HTTPException(
                status_code=400, detail="Invalid or expired refresh token"
            )

        user = self.user_repo.get_by_id(payload.sub)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        return self.create_tokens(user)


class VerifyTokenUseCase(BaseAuthUseCase):
    """Validate token and return User."""

    def execute(self, token: str) -> UserEntity:
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user = self.user_repo.get_by_id(payload.sub)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user


class ChangePasswordUseCase(BaseAuthUseCase):
    """Change user password."""

    def execute(self, user: UserEntity, old_password: str, new_password: str) -> bool:
        if not user.account_id:
            raise HTTPException(status_code=400, detail="User has no account")

        account = self.account_repo.get_by_id(user.account_id)
        if not account:
            raise HTTPException(status_code=400, detail="Account not found")

        if not verify_password(old_password, account.hash_password):
            raise HTTPException(status_code=400, detail="Incorrect old password")

        account.hash_password = get_password_hash(new_password)
        self.account_repo.update(account)
        return True


class CreateAccountUseCase:
    """Creates a new DB account and strong random password. Typically used internally by User generation."""

    def __init__(self, account_repo: AccountRepository):
        self.account_repo = account_repo

    def execute(self) -> Tuple[Account, str]:
        password = self._generate_strong_password()
        account = Account(hash_password=hash_password(password))
        saved = self.account_repo.save(account)
        return saved, password

    def _generate_strong_password(self) -> str:
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "@#$!%*?&"

        password_chars = [
            random.choice(uppercase),
            random.choice(lowercase),
            random.choice(digits),
            random.choice(symbols),
        ]
        all_chars = lowercase + uppercase + digits + symbols
        length = random.randint(10, 12)
        for _ in range(length - 4):
            password_chars.append(random.choice(all_chars))

        random.shuffle(password_chars)
        return "".join(password_chars)
