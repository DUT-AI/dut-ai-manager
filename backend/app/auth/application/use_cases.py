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
from app.shared.application.query_support_utils import build_query_support
from app.shared.application.response import BadRequestException
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.domain.entity import UserEntity, UserStatus
from app.user.infrastructure.repository import UserRepository
from app.utils.password import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    get_password_hash,
    hash_password,
    verify_password,
)


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
            email=user.email,
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
        # 1. Tìm user theo email sử dụng get_one & QuerySupport
        # Cần include role và permissions để to_entity trả về đầy đủ permissions
        user_qs = build_query_support(
            filters=[
                FilterCriterion(field="email", operator=FilterOperator.EQ, value=email)
            ],
            include=[
                "role",
                "role.role_permissions",
                "role.role_permissions.permission",
            ],
        )
        user = self.user_repo.get_one(user_qs)

        if not user:
            raise BadRequestException(status_code=401, message="User not found")

        if user.status == UserStatus.INACTIVE:
            raise BadRequestException(status_code=401, message="Account is inactive")

        # 2. Tìm account theo user_id sử dụng get_one & QuerySupport
        account_qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="user_id", operator=FilterOperator.EQ, value=user.id
                )
            ]
        )
        account = self.account_repo.get_one(account_qs)

        if not account or not verify_password(password, account.hash_password):
            raise BadRequestException(
                status_code=401, message="Incorrect email or password"
            )

        access_token, refresh_token = self.create_tokens(user)
        return user, access_token, refresh_token


class RefreshTokenUseCase(BaseAuthUseCase):
    """Issue new tokens given a valid refresh token."""

    def execute(self, refresh_token_str: str) -> Tuple[str, str]:
        payload = decode_refresh_token(refresh_token_str)
        if not payload:
            raise BadRequestException(
                status_code=400, message="Invalid or expired refresh token"
            )

        # Sử dụng get_one để load role/permissions
        user_qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="id", operator=FilterOperator.EQ, value=payload.sub
                )
            ],
            include=[
                "role",
                "role.role_permissions",
                "role.role_permissions.permission",
            ],
        )
        user = self.user_repo.get_one(user_qs)
        if not user:
            raise BadRequestException(status_code=400, message="User not found")

        return self.create_tokens(user)


class ChangePasswordUseCase(BaseAuthUseCase):
    """Change user password."""

    def execute(self, user: UserEntity, old_password: str, new_password: str) -> bool:
        account_qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="user_id", operator=FilterOperator.EQ, value=user.id
                )
            ]
        )
        account = self.account_repo.get_one(account_qs)
        if not account:
            raise BadRequestException(status_code=400, message="Account not found")

        if not verify_password(old_password, account.hash_password):
            raise BadRequestException(status_code=400, message="Incorrect old password")

        account.hash_password = get_password_hash(new_password)
        self.account_repo.update(account)
        return True


class CreateAccountUseCase:
    """Creates a new DB account and strong random password. Typically used internally by User generation."""

    def __init__(self, account_repo: AccountRepository):
        self.account_repo = account_repo

    def execute(self, user_id: Optional[int] = None) -> Tuple[Account, str]:
        password = self._generate_strong_password()
        account = Account(hash_password=hash_password(password), user_id=user_id)
        saved = self.account_repo.add(account)
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
